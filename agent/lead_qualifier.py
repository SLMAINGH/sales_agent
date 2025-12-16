"""
Lead qualifier using LLM analysis.
"""
import json
from typing import Dict, Any
from agent.schemas import Lead, LeadQualification
from agent.prompts import get_qualification_system_prompt
from model.llm import call_llm


class LeadQualifier:
    """Qualifies leads based on profile and company data."""

    def __init__(self, campaign_context: str, model: str = "gpt-4o-mini"):
        self.campaign_context = campaign_context
        self.model = model

    async def qualify_lead(
        self,
        lead: Lead,
        profile_data: Dict[str, Any],
        company_data: Dict[str, Any],
    ) -> LeadQualification:
        """
        Analyze lead and return qualification.

        Args:
            lead: Lead information
            profile_data: Aggregated profile research data
            company_data: Aggregated company research data

        Returns:
            LeadQualification with score, fit reasons, red flags, insights, priority
        """
        system_prompt = get_qualification_system_prompt(self.campaign_context)

        # Format data for LLM
        profile_summary = self._format_profile_data(profile_data)
        company_summary = self._format_company_data(company_data)

        prompt = f"""Lead Information:
Name: {lead.name}
Title: {lead.title}
Company: {lead.company_name}
LinkedIn: {lead.linkedin_url}

Profile Data:
{profile_summary}

Company Data:
{company_summary}

Analyze this lead and provide:
1. Qualification score (0-100)
2. Specific reasons they're a good fit
3. Any red flags or concerns
4. Actionable insights for personalization
5. Priority level (high/medium/low)"""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                output_schema=LeadQualification,
                model=self.model,
                temperature=0.3,  # Lower temperature for more consistent scoring
            )
            return response
        except Exception as e:
            print(f"Qualification failed for {lead.name}: {e}")
            # Return default low-quality score
            return LeadQualification(
                score=30,
                fit_reasons=["Unable to complete qualification analysis"],
                red_flags=["Analysis failed - needs manual review"],
                key_insights=[],
                priority="low",
            )

    def _format_profile_data(self, profile_data: Dict[str, Any]) -> str:
        """Format profile data for LLM prompt."""
        sections = []

        # LinkedIn profile
        if "get_linkedin_profile" in profile_data:
            profile = profile_data["get_linkedin_profile"]
            if isinstance(profile, dict):
                sections.append(f"Headline: {profile.get('headline', 'N/A')}")
                sections.append(f"Location: {profile.get('location', 'N/A')}")
                sections.append(f"Summary: {profile.get('summary', 'N/A')}")

                # Experience
                if profile.get('experience'):
                    sections.append("\nRecent Experience:")
                    for exp in profile['experience'][:2]:  # Top 2
                        sections.append(f"  - {exp.get('title')} at {exp.get('company')} ({exp.get('duration')})")

                # Skills
                if profile.get('skills'):
                    sections.append(f"\nSkills: {', '.join(profile['skills'][:10])}")

        # Recent activity
        if "get_linkedin_activity" in profile_data:
            activity = profile_data["get_linkedin_activity"]
            if isinstance(activity, dict) and activity.get('posts'):
                sections.append("\nRecent Posts:")
                for post in activity['posts'][:3]:  # Top 3
                    sections.append(f"  - {post.get('text', '')[:150]}... ({post.get('date')})")

        return "\n".join(sections) if sections else "No profile data available"

    def _format_company_data(self, company_data: Dict[str, Any]) -> str:
        """Format company data for LLM prompt."""
        sections = []

        # Company profile
        if "get_linkedin_company" in company_data:
            company = company_data["get_linkedin_company"]
            if isinstance(company, dict):
                sections.append(f"Description: {company.get('description', 'N/A')}")
                sections.append(f"Industry: {company.get('industry', 'N/A')}")
                sections.append(f"Size: {company.get('company_size', 'N/A')}")
                sections.append(f"Founded: {company.get('founded', 'N/A')}")
                if company.get('specialties'):
                    sections.append(f"Specialties: {', '.join(company['specialties'])}")

        # Company news
        if "get_company_news" in company_data:
            news = company_data["get_company_news"]
            if isinstance(news, dict) and news.get('articles'):
                sections.append("\nRecent News:")
                for article in news['articles'][:3]:
                    sections.append(f"  - {article.get('title')} ({article.get('date')})")

        # Funding
        if "get_company_funding" in company_data:
            funding = company_data["get_company_funding"]
            if isinstance(funding, dict):
                sections.append(f"\nFunding: {funding.get('total_funding', 'N/A')}")
                if funding.get('last_round'):
                    last_round = funding['last_round']
                    sections.append(f"Last Round: {last_round.get('type')} - {last_round.get('amount')} ({last_round.get('date')})")

        return "\n".join(sections) if sections else "No company data available"
