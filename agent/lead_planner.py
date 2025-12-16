"""
Lead planner with company deduplication.
"""
from typing import List
from collections import defaultdict
from agent.schemas import Lead, PlannedTask, SubTask, ResearchPlan
from agent.prompts import get_planning_system_prompt
from model.llm import call_llm
from tools import TOOLS


class LeadPlanner:
    """Plans research tasks with company deduplication."""

    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def _group_by_company(self, leads: List[Lead]) -> dict:
        """Group leads by company name."""
        company_groups = defaultdict(list)
        for lead in leads:
            company_groups[lead.company_name].append(lead)
        return dict(company_groups)

    def _build_tool_schemas(self) -> str:
        """Build tool schemas for the LLM."""
        schemas = []
        for tool in TOOLS:
            schema_dict = tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
            properties = schema_dict.get('properties', {})

            param_lines = []
            for name, prop in properties.items():
                param_type = prop.get('type', 'any')
                description = prop.get('description', '')
                param_lines.append(f"  - {name}: {param_type} - {description}")

            schemas.append(f"{tool.name}: {tool.description}\nParameters:\n" + "\n".join(param_lines))

        return "\n\n".join(schemas)

    async def plan_research(
        self,
        leads: List[Lead],
        campaign_context: str,
    ) -> ResearchPlan:
        """
        Create research plan with company deduplication.

        Returns a ResearchPlan with:
        - Company research tasks (one per unique company)
        - Profile research tasks (one per lead)
        """
        if not leads:
            return ResearchPlan(tasks=[])

        # Group leads by company
        company_groups = self._group_by_company(leads)

        # Build tool schemas
        tool_schemas = self._build_tool_schemas()
        system_prompt = get_planning_system_prompt(tool_schemas)

        # Create prompt
        lead_summaries = "\n".join([
            f"- {lead.name} ({lead.title}) at {lead.company_name} [ID: {lead.id}]"
            for lead in leads
        ])

        company_summary = "\n".join([
            f"- {company}: {len(lead_list)} leads"
            for company, lead_list in company_groups.items()
        ])

        prompt = f"""Campaign Context:
{campaign_context}

Leads to research ({len(leads)} total):
{lead_summaries}

Companies ({len(company_groups)} unique):
{company_summary}

Create an efficient research plan:
1. ONE company_research task per unique company (include all lead_ids for that company)
2. ONE profile_research task per lead
3. Keep subtasks specific and actionable"""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                output_schema=ResearchPlan,
                model=self.model,
            )
            return response
        except Exception as e:
            print(f"Planning error: {e}")
            # Fallback: create manual plan
            return self._create_fallback_plan(leads, company_groups)

    def _create_fallback_plan(
        self,
        leads: List[Lead],
        company_groups: dict,
    ) -> ResearchPlan:
        """Create a basic plan if LLM fails."""
        tasks = []
        task_id = 1

        # Company research tasks
        for company, company_leads in company_groups.items():
            tasks.append(PlannedTask(
                id=task_id,
                type="company_research",
                description=f"Research {company}",
                company=company,
                lead_ids=[lead.id for lead in company_leads],
                sub_tasks=[
                    SubTask(id=1, description=f"Get LinkedIn company page for {company}"),
                    SubTask(id=2, description=f"Get recent company posts for {company}"),
                    SubTask(id=3, description=f"Get company news for {company}"),
                ]
            ))
            task_id += 1

        # Profile research tasks
        for lead in leads:
            tasks.append(PlannedTask(
                id=task_id,
                type="profile_research",
                description=f"Research {lead.name}",
                lead_id=lead.id,
                sub_tasks=[
                    SubTask(id=1, description=f"Get LinkedIn profile for {lead.linkedin_url}"),
                    SubTask(id=2, description=f"Get recent activity for {lead.linkedin_url}"),
                ]
            ))
            task_id += 1

        return ResearchPlan(tasks=tasks)
