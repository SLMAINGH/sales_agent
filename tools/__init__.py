"""
Tool registry for the sales qualification agent.
"""
from tools.linkedin.profile import get_linkedin_profile, get_linkedin_activity
from tools.linkedin.company import get_linkedin_company, get_company_posts
from tools.company.news import research_company


# All available tools
TOOLS = [
    get_linkedin_profile,
    get_linkedin_activity,
    get_linkedin_company,
    get_company_posts,
    research_company,
]


__all__ = [
    "TOOLS",
    "get_linkedin_profile",
    "get_linkedin_activity",
    "get_linkedin_company",
    "get_company_posts",
    "research_company",
]
