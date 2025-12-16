"""
FastAPI server for sales qualification agent - Clay integration.
"""
import asyncio
import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
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


class BatchLeadsOutput(BaseModel):
    """Output model for batch processing."""
    results: list[LeadOutput]
    total_processed: int
    total_qualified: int


# Default campaign context
DEFAULT_CAMPAIGN_CONTEXT = """
We're selling an AI-powered code review tool for engineering teams.

Target Profile:
- VPs/Directors of Engineering at Series A-C startups
- Company size: 50-500 employees
- Tech-forward companies building software products
- Pain points: Code quality, review bottlenecks, onboarding new devs, scaling engineering processes

Value Proposition:
- Reduce code review time by 40%
- Catch bugs before they reach production
- Onboard new engineers 2x faster
- Automated code quality insights

Pricing: Starting at $500/month for teams of 10-50 engineers
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


def convert_qualified_lead_to_output(ql: QualifiedLead) -> LeadOutput:
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
    campaign_context: Optional[str] = None
):
    """
    Qualify a single lead and generate personalized copy.

    Perfect for Clay's HTTP API enrichment - send one lead, get back qualification data.
    """
    try:
        # Convert input to internal Lead model
        lead = Lead(
            id=lead_input.id or f"lead_{lead_input.name.replace(' ', '_').lower()}",
            name=lead_input.name,
            linkedin_url=lead_input.linkedin_url,
            company_name=lead_input.company_name,
            title=lead_input.title,
        )

        # Initialize agent
        context = campaign_context or DEFAULT_CAMPAIGN_CONTEXT
        agent = SalesQualificationAgent(
            campaign_context=context,
            model="gpt-4o-mini",
            copy_model="gpt-4o",
            qualification_threshold=50,
        )

        # Process lead
        qualified_leads = await agent.process_leads([lead], verbose=False)

        if not qualified_leads:
            raise HTTPException(status_code=500, detail="Failed to process lead")

        # Convert to output format
        return convert_qualified_lead_to_output(qualified_leads[0])

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing lead: {str(e)}")


async def process_lead_and_webhook(lead_input: WebhookLeadInput):
    """
    Background task: Process lead and send results to webhook.
    """
    try:
        # Convert input to internal Lead model
        lead = Lead(
            id=lead_input.id or f"lead_{lead_input.name.replace(' ', '_').lower()}",
            name=lead_input.name,
            linkedin_url=lead_input.linkedin_url,
            company_name=lead_input.company_name,
            title=lead_input.title,
        )

        # Initialize agent
        context = lead_input.campaign_context or DEFAULT_CAMPAIGN_CONTEXT
        agent = SalesQualificationAgent(
            campaign_context=context,
            model="gpt-4o-mini",
            copy_model="gpt-4o",
            qualification_threshold=50,
        )

        # Process lead
        qualified_leads = await agent.process_leads([lead], verbose=False)

        if not qualified_leads:
            # Send error to webhook
            error_response = {
                "status": "error",
                "lead_id": lead_input.id,
                "error": "Failed to process lead"
            }
            requests.post(lead_input.webhook_url, json=error_response, timeout=10)
            return

        # Convert to output format
        result = convert_qualified_lead_to_output(qualified_leads[0])

        # Add status field for webhook
        webhook_payload = {
            "status": "success",
            "lead_id": lead_input.id,
            "data": result.dict()
        }

        # Send results to webhook
        requests.post(lead_input.webhook_url, json=webhook_payload, timeout=10)

    except Exception as e:
        # Send error to webhook
        error_response = {
            "status": "error",
            "lead_id": lead_input.id,
            "error": str(e)
        }
        try:
            requests.post(lead_input.webhook_url, json=error_response, timeout=10)
        except:
            pass  # If webhook fails, nothing we can do


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
