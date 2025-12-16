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
    Requires RAPIDAPI_KEY environment variable.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # RapidAPI implementation
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
    Requires RAPIDAPI_KEY environment variable.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # RapidAPI implementation
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
