"""
Main sales qualification agent orchestrator.
"""
import asyncio
from typing import List, Optional
from agent.schemas import Lead, QualifiedLead, ResearchSummary
from agent.lead_planner import LeadPlanner
from agent.lead_executor import LeadExecutor
from agent.lead_qualifier import LeadQualifier
from agent.copy_generator import CopyGenerator
from utils.context import ToolContextManager


class SalesQualificationAgent:
    """
    Main agent that orchestrates lead qualification and copy generation.

    Pipeline:
    1. Plan research (with company deduplication)
    2. Execute research (parallel)
    3. Qualify each lead
    4. Generate copy for qualified leads
    """

    def __init__(
        self,
        campaign_context: str,
        model: str = "gpt-4o-mini",
        copy_model: str = "gpt-4o",
        context_dir: str = ".leads/context",
        qualification_threshold: int = 50,
    ):
        """
        Initialize the sales qualification agent.

        Args:
            campaign_context: Description of what you're selling and target persona
            model: Model for planning/qualification
            copy_model: Model for copy generation (typically better model)
            context_dir: Directory to save research data
            qualification_threshold: Minimum score to generate copy
        """
        self.campaign_context = campaign_context
        self.qualification_threshold = qualification_threshold

        # Initialize components
        self.context_manager = ToolContextManager(context_dir, model)
        self.planner = LeadPlanner(model)
        self.executor = LeadExecutor(self.context_manager, model)
        self.qualifier = LeadQualifier(campaign_context, model)
        self.copy_generator = CopyGenerator(campaign_context, copy_model)

    async def process_leads(
        self,
        leads: List[Lead],
        verbose: bool = True,
    ) -> List[QualifiedLead]:
        """
        Process a batch of leads.

        Args:
            leads: List of leads to process
            verbose: Print progress messages

        Returns:
            List of QualifiedLead objects with scores and personalized copy
        """
        if not leads:
            return []

        if verbose:
            print(f"\n🚀 Processing {len(leads)} leads...")
            print(f"📊 Campaign: {self.campaign_context[:100]}...\n")

        # Phase 1: Plan research
        if verbose:
            print("📋 Phase 1: Planning research...")
        research_plan = await self.planner.plan_research(leads, self.campaign_context)

        if verbose:
            company_tasks = len([t for t in research_plan.tasks if t.type == "company_research"])
            profile_tasks = len([t for t in research_plan.tasks if t.type == "profile_research"])
            print(f"   ✓ Created {len(research_plan.tasks)} tasks ({company_tasks} company, {profile_tasks} profile)")

        # Phase 2: Execute research
        if verbose:
            print("\n🔍 Phase 2: Executing research...")

        def on_task_start(task):
            if verbose:
                print(f"   → {task.description}")

        def on_task_complete(task, success):
            if verbose:
                status = "✓" if success else "✗"
                print(f"   {status} {task.description}")

        await self.executor.execute_research(
            research_plan,
            on_task_start=on_task_start,
            on_task_complete=on_task_complete,
        )

        # Phase 3 & 4: Qualify and generate copy (parallel per lead)
        if verbose:
            print(f"\n🎯 Phase 3: Qualifying leads and generating copy...")

        qualified_leads = await asyncio.gather(*[
            self._process_single_lead(lead, verbose)
            for lead in leads
        ])

        # Summary
        if verbose:
            high_priority = len([l for l in qualified_leads if l.qualification.priority == "high"])
            medium_priority = len([l for l in qualified_leads if l.qualification.priority == "medium"])
            low_priority = len([l for l in qualified_leads if l.qualification.priority == "low"])
            with_copy = len([l for l in qualified_leads if l.personalized_copy is not None])

            print(f"\n✅ Processing complete!")
            print(f"   High priority: {high_priority}")
            print(f"   Medium priority: {medium_priority}")
            print(f"   Low priority: {low_priority}")
            print(f"   Copy generated: {with_copy}/{len(qualified_leads)}")

        return qualified_leads

    async def _process_single_lead(
        self,
        lead: Lead,
        verbose: bool,
    ) -> QualifiedLead:
        """Process a single lead (qualification + copy generation)."""
        # Load research data
        profile_data = self.context_manager.get_context_for_lead(lead.id)
        company_data = self.context_manager.get_context_for_company(lead.company_name)

        # Qualify
        if verbose:
            print(f"   ⚖️  Qualifying {lead.name}...")
        qualification = await self.qualifier.qualify_lead(lead, profile_data, company_data)

        if verbose:
            print(f"      Score: {qualification.score}/100 ({qualification.priority} priority)")

        # Generate copy if qualified
        personalized_copy = None
        if qualification.score >= self.qualification_threshold:
            if verbose:
                print(f"   ✍️  Generating copy for {lead.name}...")
            personalized_copy = await self.copy_generator.generate_copy(
                lead, qualification, profile_data, company_data
            )

        # Build research summary
        research_summary = self._build_research_summary(profile_data, company_data)

        return QualifiedLead(
            lead=lead,
            qualification=qualification,
            personalized_copy=personalized_copy,
            research_summary=research_summary,
        )

    def _build_research_summary(self, profile_data, company_data) -> ResearchSummary:
        """Build a summary of research data collected."""
        profile_highlights = []
        company_highlights = []
        recent_activity = []

        # Profile highlights
        if "get_linkedin_profile" in profile_data:
            profile = profile_data["get_linkedin_profile"]
            if isinstance(profile, dict):
                if profile.get('headline'):
                    profile_highlights.append(profile['headline'])
                if profile.get('experience'):
                    exp = profile['experience'][0]
                    profile_highlights.append(f"{exp.get('title')} at {exp.get('company')}")

        # Company highlights
        if "get_linkedin_company" in company_data:
            company = company_data["get_linkedin_company"]
            if isinstance(company, dict):
                if company.get('company_size'):
                    company_highlights.append(f"Size: {company['company_size']}")
                if company.get('industry'):
                    company_highlights.append(f"Industry: {company['industry']}")

        # Recent activity
        if "get_linkedin_activity" in profile_data:
            activity = profile_data["get_linkedin_activity"]
            if isinstance(activity, dict) and activity.get('posts'):
                for post in activity['posts'][:2]:
                    text = post.get('text', '')[:100]
                    recent_activity.append(f"{text}...")

        return ResearchSummary(
            profile_highlights=profile_highlights or ["No profile data"],
            company_highlights=company_highlights or ["No company data"],
            recent_activity=recent_activity or ["No recent activity"],
        )
