"""
FastAPI server for sales qualification agent - Clay integration.
"""
import asyncio
import os
import logging
from typing import Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import requests
from agent.schemas import Lead, QualifiedLead
from agent.sales_agent import SalesQualificationAgent


# API Models
class LeadInput(BaseModel):
    """Input model for a single lead."""
    name: str = Field(..., description="Full name of the lead")
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    company_name: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    id: Optional[str] = Field(None, description="Optional lead ID")


class WebhookLeadInput(BaseModel):
    """Input model for webhook-based async processing."""
    name: str = Field(..., description="Full name of the lead")
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    company_name: str = Field(..., description="Company name")
    title: str = Field(..., description="Job title")
    webhook_url: str = Field(..., description="Webhook URL to send results to")
    id: Optional[str] = Field(None, description="Optional lead ID")
    campaign_context: Optional[str] = Field(None, description="Optional custom campaign context")


class BatchLeadsInput(BaseModel):
    """Input model for batch lead processing."""
    leads: list[LeadInput] = Field(..., description="List of leads to process")
    campaign_context: Optional[str] = Field(None, description="Optional custom campaign context")


class QualificationOutput(BaseModel):
    """Output model for qualification results."""
    score: int
    priority: str
    fit_reasons: list[str]
    red_flags: list[str]
    key_insights: list[str]


class PersonalizedCopyOutput(BaseModel):
    """Output model for personalized copy."""
    subject_line: str
    email_body: str
    linkedin_message: str
    talking_points: list[str]


class ResearchSummaryOutput(BaseModel):
    """Output model for research summary."""
    profile_highlights: list[str]
    company_highlights: list[str]
    recent_activity: list[str]


class LeadOutput(BaseModel):
    """Output model for qualified lead."""
    lead: LeadInput
    qualification: QualificationOutput
    personalized_copy: Optional[PersonalizedCopyOutput]
    research_summary: ResearchSummaryOutput
    execution_logs: Optional[list[str]] = None  # Verbose execution logs
    processing_time_seconds: Optional[float] = None


class BatchLeadsOutput(BaseModel):
    """Output model for batch processing."""
    results: list[LeadOutput]
    total_processed: int
    total_qualified: int


# Default campaign context
DEFAULT_CAMPAIGN_CONTEXT = """
We are selling Niteco's "Sitecore Modernization & XM Cloud Migration" services.

Our Value Proposition:
We help enterprises escape legacy Sitecore monolithic versions (XP 9/10) and migrate to a modern, composable stack (XM Cloud + Next.js) faster and with less risk than generalist agencies. We use a proprietary "Audit & Roadmap" methodology to guarantee fixed costs and timelines.

Target Profile:
- Role: CIOs, CTOs, VPs of Digital, and CMOs.
- Company Size: Mid-to-Enterprise (Revenue $200M+, 500+ employees).
- Industries: Manufacturing, Retail/Distribution, Healthcare, Finance.
- Tech Stack: Currently running Sitecore XP (Versions 8.x, 9.x, or 10.x) on-premise or via Azure PaaS.

Key Pain Points (The "Why Now"):
1. "The Monolith Trap": High Azure infrastructure costs and slow deployment cycles on legacy Sitecore XP.
2. "XM Cloud Anxiety": They know they need to move to SaaS/Headless (XM Cloud) but fear the complexity of rewriting the front-end (Next.js).
3. "Performance Issues": Slow page loads affecting Core Web Vitals and SEO rankings.
4. "Talent Gap": Struggle to find developers skilled in both legacy .NET Sitecore and modern React/Next.js.

The Offer (The Hook):
A "Sitecore Modernization Audit." We will analyze their current codebase and infrastructure to provide a fixed-price/fixed-timeline roadmap to XM Cloud, de-risking the migration.

Niteco Differentiators:
- Deep .NET & Sitecore Gold Partner pedigree.
- Proven "Upgrade Accelerator" methodology (similar to our Optimizely framework).
- Global delivery model ensuring 24/7 progress and cost-efficiency.
"""


# Initialize FastAPI app
app = FastAPI(
    title="Sales Qualification API",
    description="AI-powered lead qualification and personalized copy generation",
    version="1.0.0"
)

# Add CORS middleware for Clay integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to Clay's domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LogCapture:
    """Capture logs during execution."""
    def __init__(self):
        self.logs = []

    def log(self, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        logger.info(message)


def convert_qualified_lead_to_output(ql: QualifiedLead, logs: Optional[list[str]] = None, processing_time: Optional[float] = None) -> LeadOutput:
    """Convert internal QualifiedLead to API output format."""
    return LeadOutput(
        lead=LeadInput(
            id=ql.lead.id,
            name=ql.lead.name,
            linkedin_url=ql.lead.linkedin_url,
            company_name=ql.lead.company_name,
            title=ql.lead.title,
        ),
        qualification=QualificationOutput(
            score=ql.qualification.score,
            priority=ql.qualification.priority,
            fit_reasons=ql.qualification.fit_reasons,
            red_flags=ql.qualification.red_flags,
            key_insights=ql.qualification.key_insights,
        ),
        personalized_copy=PersonalizedCopyOutput(
            subject_line=ql.personalized_copy.subject_line,
            email_body=ql.personalized_copy.email_body,
            linkedin_message=ql.personalized_copy.linkedin_message,
            talking_points=ql.personalized_copy.talking_points,
        ) if ql.personalized_copy else None,
        research_summary=ResearchSummaryOutput(
            profile_highlights=ql.research_summary.profile_highlights,
            company_highlights=ql.research_summary.company_highlights,
            recent_activity=ql.research_summary.recent_activity,
        ),
        execution_logs=logs,
        processing_time_seconds=processing_time,
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Sales Qualification API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "rapidapi_key_configured": bool(os.getenv("RAPIDAPI_KEY")),
    }


@app.post("/qualify", response_model=LeadOutput)
async def qualify_single_lead(
    lead_input: LeadInput,
    campaign_context: Optional[str] = None,
    verbose: bool = False
):
    """
    Qualify a single lead and generate personalized copy.

    Perfect for Clay's HTTP API enrichment - send one lead, get back qualification data.

    Set verbose=true to get detailed execution logs in the response.
    """
    import time
    start_time = time.time()
    log_capture = LogCapture()

    try:
        log_capture.log(f"🚀 Starting qualification for: {lead_input.name} at {lead_input.company_name}")

        # Convert input to internal Lead model
        lead = Lead(
            id=lead_input.id or f"lead_{lead_input.name.replace(' ', '_').lower()}",
            name=lead_input.name,
            linkedin_url=lead_input.linkedin_url,
            company_name=lead_input.company_name,
            title=lead_input.title,
        )
        log_capture.log(f"✓ Lead ID: {lead.id}")

        # Initialize agent
        context = campaign_context or DEFAULT_CAMPAIGN_CONTEXT
        log_capture.log("⚙️  Initializing SalesQualificationAgent...")
        agent = SalesQualificationAgent(
            campaign_context=context,
            model="gpt-4o-mini",
            copy_model="gpt-4o",
            qualification_threshold=50,
        )
        log_capture.log("✓ Agent initialized")

        # Process lead
        log_capture.log("🔍 Starting lead processing (planning, research, qualification, copy generation)...")
        qualified_leads = await agent.process_leads([lead], verbose=True)

        if not qualified_leads:
            log_capture.log("❌ No qualified leads returned")
            raise HTTPException(status_code=500, detail="Failed to process lead")

        log_capture.log(f"✅ Qualification complete! Score: {qualified_leads[0].qualification.score}/100")

        processing_time = time.time() - start_time
        log_capture.log(f"⏱️  Total processing time: {processing_time:.2f}s")

        # Convert to output format
        return convert_qualified_lead_to_output(
            qualified_leads[0],
            logs=log_capture.logs if verbose else None,
            processing_time=processing_time
        )

    except Exception as e:
        log_capture.log(f"❌ Error: {str(e)}")
        logger.error(f"Error processing lead {lead_input.name}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing lead: {str(e)}")


async def process_lead_and_webhook(lead_input: WebhookLeadInput):
    """
    Background task: Process lead and send results to webhook.
    """
    try:
        logger.info(f"🚀 WEBHOOK PROCESSING START: {lead_input.name} at {lead_input.company_name}")

        # Convert input to internal Lead model
        lead = Lead(
            id=lead_input.id or f"lead_{lead_input.name.replace(' ', '_').lower()}",
            name=lead_input.name,
            linkedin_url=lead_input.linkedin_url,
            company_name=lead_input.company_name,
            title=lead_input.title,
        )
        logger.info(f"Lead ID: {lead.id}")

        # Initialize agent
        context = lead_input.campaign_context or DEFAULT_CAMPAIGN_CONTEXT
        logger.info("Initializing SalesQualificationAgent...")
        agent = SalesQualificationAgent(
            campaign_context=context,
            model="gpt-4o-mini",
            copy_model="gpt-4o",
            qualification_threshold=50,
        )

        # Process lead (verbose=True to see all agent activity in logs)
        logger.info("Starting lead processing...")
        qualified_leads = await agent.process_leads([lead], verbose=True)

        if not qualified_leads:
            logger.error("No qualified leads returned!")
            error_response = {
                "status": "error",
                "lead_id": lead_input.id,
                "error": "Failed to process lead"
            }
            requests.post(lead_input.webhook_url, json=error_response, timeout=10)
            return

        # Convert to output format
        result = convert_qualified_lead_to_output(qualified_leads[0])

        logger.info(f"✅ Processing complete! Score: {qualified_leads[0].qualification.score}/100")
        logger.info(f"Sending results to webhook: {lead_input.webhook_url}")

        # Add status field for webhook
        webhook_payload = {
            "status": "success",
            "lead_id": lead_input.id,
            "data": result.dict()
        }

        # Send results to webhook
        webhook_response = requests.post(lead_input.webhook_url, json=webhook_payload, timeout=10)
        logger.info(f"Webhook delivered: {webhook_response.status_code}")

    except Exception as e:
        logger.error(f"❌ ERROR processing lead: {str(e)}", exc_info=True)
        # Send error to webhook
        error_response = {
            "status": "error",
            "lead_id": lead_input.id,
            "error": str(e)
        }
        try:
            requests.post(lead_input.webhook_url, json=error_response, timeout=10)
            logger.info("Error sent to webhook")
        except Exception as webhook_error:
            logger.error(f"Failed to send error to webhook: {webhook_error}")


@app.post("/qualify/webhook")
async def qualify_lead_webhook(lead_input: WebhookLeadInput, background_tasks: BackgroundTasks):
    """
    Qualify a lead asynchronously and send results to webhook URL.

    Perfect for Clay when processing time might be too long for synchronous response.
    Returns immediately with 202 Accepted, then sends results to webhook_url when done.

    Request body must include:
    - name, linkedin_url, company_name, title (lead data)
    - webhook_url (where to send results)

    The webhook will receive:
    {
        "status": "success" | "error",
        "lead_id": "...",
        "data": {...}  // Full LeadOutput if success
        "error": "..."  // Error message if error
    }
    """
    # Add processing task to background
    background_tasks.add_task(process_lead_and_webhook, lead_input)

    # Return immediately
    return {
        "status": "accepted",
        "message": "Lead queued for processing. Results will be sent to webhook.",
        "lead_id": lead_input.id or f"lead_{lead_input.name.replace(' ', '_').lower()}",
        "webhook_url": lead_input.webhook_url
    }


@app.post("/qualify/batch", response_model=BatchLeadsOutput)
async def qualify_batch_leads(batch_input: BatchLeadsInput):
    """
    Qualify multiple leads in a single request.

    Useful for batch processing or if Clay supports batch API calls.
    Automatically deduplicates company research for efficiency.
    """
    try:
        # Convert inputs to internal Lead models
        leads = [
            Lead(
                id=lead.id or f"lead_{i}",
                name=lead.name,
                linkedin_url=lead.linkedin_url,
                company_name=lead.company_name,
                title=lead.title,
            )
            for i, lead in enumerate(batch_input.leads)
        ]

        # Initialize agent
        context = batch_input.campaign_context or DEFAULT_CAMPAIGN_CONTEXT
        agent = SalesQualificationAgent(
            campaign_context=context,
            model="gpt-4o-mini",
            copy_model="gpt-4o",
            qualification_threshold=50,
        )

        # Process leads
        qualified_leads = await agent.process_leads(leads, verbose=False)

        # Convert to output format
        results = [convert_qualified_lead_to_output(ql) for ql in qualified_leads]

        return BatchLeadsOutput(
            results=results,
            total_processed=len(qualified_leads),
            total_qualified=len([r for r in results if r.qualification.score >= 50]),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing batch: {str(e)}")


@app.post("/qualify/async")
async def qualify_async(batch_input: BatchLeadsInput, background_tasks: BackgroundTasks):
    """
    Start async batch processing (returns immediately with job ID).

    For large batches - returns job ID that can be polled for results.
    Note: Requires a job queue/database for production use.
    """
    # TODO: Implement job queue (Redis/Celery) for production
    return {
        "status": "queued",
        "message": "Async processing not yet implemented. Use /qualify/batch for now.",
        "job_id": None,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
