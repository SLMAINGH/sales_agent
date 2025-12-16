"""
LinkedIn company scraping tools.
"""
import os
import requests
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class LinkedInCompanyInput(BaseModel):
    """Input for LinkedIn company tool."""
    company_name: str = Field(description="Company name to search for")


@tool("get_linkedin_company", args_schema=LinkedInCompanyInput)
def get_linkedin_company(company_name: str) -> Dict[str, Any]:
    """
    Fetches LinkedIn company page data including description, size, industry, headquarters, and recent updates.
    Useful for understanding company context, stage, and focus areas.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        # Mock data for testing
        return {
            "name": company_name,
            "description": "Leading software company building AI-powered developer tools...",
            "industry": "Software Development",
            "company_size": "51-200 employees",
            "headquarters": "San Francisco, CA",
            "founded": "2019",
            "specialties": ["AI/ML", "Developer Tools", "SaaS"],
            "website": "https://example.com",
            "recent_updates": [
                {
                    "text": "Excited to announce our Series B funding of $50M!",
                    "date": "2024-01-20"
                }
            ]
        }

    # Actual RapidAPI implementation
    url = "https://linkedin-data-api.p.rapidapi.com/get-company"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
    }
    params = {"company": company_name}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch company: {str(e)}"}


@tool("get_company_posts", args_schema=LinkedInCompanyInput)
def get_company_posts(company_name: str) -> Dict[str, Any]:
    """
    Fetches recent posts from a company's LinkedIn page.
    Useful for finding timely conversation starters and understanding company priorities.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        # Mock data for testing
        return {
            "posts": [
                {
                    "text": "Join us at TechConf 2024! Our CEO will be speaking about the future of AI...",
                    "date": "2024-01-18",
                    "likes": 567
                },
                {
                    "text": "We're hiring! Looking for senior engineers to join our AI team...",
                    "date": "2024-01-15",
                    "likes": 234
                }
            ]
        }

    # Actual RapidAPI implementation
    url = "https://linkedin-data-api.p.rapidapi.com/get-company-posts"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
    }
    params = {"company": company_name}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch company posts: {str(e)}"}
