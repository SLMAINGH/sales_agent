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
    Uses Fresh LinkedIn Scraper API via RapidAPI.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # Fresh LinkedIn Scraper API - company endpoint
    url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/company"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "fresh-linkedin-scraper-api.p.rapidapi.com"
    }
    params = {"company_name": company_name}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data or not data.get("success", True):
            return {"error": f"LinkedIn API error: {data.get('message', 'Unknown error')}"}

        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"LinkedIn API HTTP error {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"Failed to fetch company: {str(e)}"}


@tool("get_company_posts", args_schema=LinkedInCompanyInput)
def get_company_posts(company_name: str) -> Dict[str, Any]:
    """
    Fetches recent posts from a company's LinkedIn page.
    Useful for finding timely conversation starters and understanding company priorities.
    Uses Fresh LinkedIn Scraper API via RapidAPI.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # Fresh LinkedIn Scraper API - company posts endpoint
    url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/company-posts"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "fresh-linkedin-scraper-api.p.rapidapi.com"
    }
    params = {"company_name": company_name}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if "error" in data or not data.get("success", True):
            return {"error": f"LinkedIn API error: {data.get('message', 'Unknown error')}"}

        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"LinkedIn API HTTP error {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"Failed to fetch company posts: {str(e)}"}
