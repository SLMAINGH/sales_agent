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
            # Check if it's an error response
            if isinstance(profile, dict) and "error" not in profile:
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
            elif isinstance(profile, dict) and "error" in profile:
                sections.append(f"⚠️ Profile data unavailable: {profile['error']}")

        # Recent activity
        if "get_linkedin_activity" in profile_data:
            activity = profile_data["get_linkedin_activity"]
            if isinstance(activity, dict) and "error" not in activity and activity.get('posts'):
                sections.append("\nRecent Posts:")
                for post in activity['posts'][:3]:  # Top 3
                    sections.append(f"  - {post.get('text', '')[:150]}... ({post.get('date')})")
            elif isinstance(activity, dict) and "error" in activity:
                sections.append(f"\n⚠️ Activity data unavailable: {activity['error']}")

        return "\n".join(sections) if sections else "No profile data available - LinkedIn scraping may have failed"

    def _format_company_data(self, company_data: Dict[str, Any]) -> str:
        """Format company data for LLM prompt."""
        sections = []

        # Company profile
        if "get_linkedin_company" in company_data:
            company = company_data["get_linkedin_company"]
            if isinstance(company, dict) and "error" not in company:
                sections.append(f"Description: {company.get('description', 'N/A')}")
                sections.append(f"Industry: {company.get('industry', 'N/A')}")
                sections.append(f"Size: {company.get('company_size', 'N/A')}")
                sections.append(f"Founded: {company.get('founded', 'N/A')}")
                if company.get('specialties'):
                    sections.append(f"Specialties: {', '.join(company['specialties'])}")
            elif isinstance(company, dict) and "error" in company:
                sections.append(f"⚠️ Company LinkedIn data unavailable: {company['error']}")

        # Company posts
        if "get_company_posts" in company_data:
            posts = company_data["get_company_posts"]
            if isinstance(posts, dict) and "error" not in posts and posts.get('posts'):
                sections.append("\nRecent Company Posts:")
                for post in posts['posts'][:3]:
                    sections.append(f"  - {post.get('text', '')[:150]}...")
            elif isinstance(posts, dict) and "error" in posts:
                sections.append(f"\n⚠️ Company posts unavailable: {posts['error']}")

        # Perplexity company research
        if "research_company" in company_data:
            research = company_data["research_company"]
            if isinstance(research, dict) and "error" not in research and research.get('research'):
                sections.append("\nCompany Research (News, Funding, Recent Developments):")
                sections.append(research['research'])
            elif isinstance(research, dict) and "error" in research:
                sections.append(f"\n⚠️ Company research unavailable: {research['error']}")

        return "\n".join(sections) if sections else "No company data available - Company research may have failed"
