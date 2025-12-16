"""
Copy generator for personalized outreach.
"""
import json
from typing import Dict, Any
from agent.schemas import Lead, LeadQualification, PersonalizedCopy
from agent.prompts import get_copy_generation_system_prompt
from model.llm import call_llm


class CopyGenerator:
    """Generates personalized outreach copy."""

    def __init__(self, campaign_context: str, model: str = "gpt-4o"):
        self.campaign_context = campaign_context
        self.model = model  # Use better model for copy generation

    async def generate_copy(
        self,
        lead: Lead,
        qualification: LeadQualification,
        profile_data: Dict[str, Any],
        company_data: Dict[str, Any],
    ) -> PersonalizedCopy:
        """
        Generate personalized outreach copy.

        Args:
            lead: Lead information
            qualification: Qualification results
            profile_data: Profile research data
            company_data: Company research data

        Returns:
            PersonalizedCopy with subject, email, LinkedIn message, talking points
        """
        system_prompt = get_copy_generation_system_prompt(self.campaign_context)

        # Extract key personalization hooks
        recent_activity = self._extract_recent_activity(profile_data)
        company_news = self._extract_company_news(company_data)

        prompt = f"""Lead Information:
Name: {lead.name}
Title: {lead.title}
Company: {lead.company_name}

Qualification Results:
Score: {qualification.score}/100
Priority: {qualification.priority}
Key Insights: {', '.join(qualification.key_insights)}

Recent Activity (for personalization):
{recent_activity}

Company News (for timing/relevance):
{company_news}

Generate personalized outreach copy:
1. Email subject line (reference their activity or company news)
2. Email body (2-3 short paragraphs)
3. LinkedIn message (3-4 sentences, more casual)
4. Talking points for calls/meetings (3-5 bullet points)

Make it feel personal, relevant, and valuable. Show you did your research."""

        try:
            response = await call_llm(
                prompt=prompt,
                system_prompt=system_prompt,
                output_schema=PersonalizedCopy,
                model=self.model,
                temperature=0.8,  # Higher temperature for more creative copy
            )
            return response
        except Exception as e:
            print(f"Copy generation failed for {lead.name}: {e}")
            # Return generic fallback copy
            return PersonalizedCopy(
                subject_line=f"Quick question about {lead.company_name}'s engineering process",
                email_body=f"Hi {lead.name.split()[0]},\n\nI noticed your role at {lead.company_name} and wanted to reach out...",
                linkedin_message=f"Hi {lead.name.split()[0]}, I'd love to connect and learn more about your work at {lead.company_name}.",
                talking_points=[
                    f"Ask about their role at {lead.company_name}",
                    "Discuss industry challenges",
                    "Share relevant case studies",
                ],
            )

    def _extract_recent_activity(self, profile_data: Dict[str, Any]) -> str:
        """Extract recent activity for personalization."""
        activity_lines = []

        if "get_linkedin_activity" in profile_data:
            activity = profile_data["get_linkedin_activity"]
            if isinstance(activity, dict) and activity.get('posts'):
                activity_lines.append("Recent LinkedIn posts:")
                for post in activity['posts'][:2]:  # Top 2
                    text = post.get('text', '')[:200]
                    date = post.get('date', 'recently')
                    activity_lines.append(f"  - {text}... (posted {date})")

        return "\n".join(activity_lines) if activity_lines else "No recent activity found"

    def _extract_company_news(self, company_data: Dict[str, Any]) -> str:
        """Extract company news for timing/relevance."""
        news_lines = []

        if "get_company_news" in company_data:
            news = company_data["get_company_news"]
            if isinstance(news, dict) and news.get('articles'):
                news_lines.append("Recent company news:")
                for article in news['articles'][:2]:
                    title = article.get('title', '')
                    date = article.get('date', '')
                    news_lines.append(f"  - {title} ({date})")

        if "get_company_posts" in company_data:
            posts = company_data["get_company_posts"]
            if isinstance(posts, dict) and posts.get('posts'):
                if not news_lines:
                    news_lines.append("Recent company updates:")
                for post in posts['posts'][:2]:
                    text = post.get('text', '')[:150]
                    news_lines.append(f"  - {text}...")

        return "\n".join(news_lines) if news_lines else "No recent news found"
