"""
LinkedIn profile scraping tool using RapidAPI.
"""
import os
import requests
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class LinkedInProfileInput(BaseModel):
    """Input for LinkedIn profile tool."""
    linkedin_url: str = Field(description="LinkedIn profile URL to scrape")


@tool("get_linkedin_profile", args_schema=LinkedInProfileInput)
def get_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
    """
    Fetches LinkedIn profile data including name, headline, summary, experience, education, and skills.
    Useful for understanding a lead's background, career trajectory, and expertise.
    Requires RAPIDAPI_KEY environment variable.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # RapidAPI implementation
    url = "https://linkedin-data-api.p.rapidapi.com/get-profile"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
    }
    params = {"url": linkedin_url}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch profile: {str(e)}"}


class LinkedInActivityInput(BaseModel):
    """Input for LinkedIn activity tool."""
    linkedin_url: str = Field(description="LinkedIn profile URL")
    limit: int = Field(default=10, description="Number of recent posts to fetch")


@tool("get_linkedin_activity", args_schema=LinkedInActivityInput)
def get_linkedin_activity(linkedin_url: str, limit: int = 10) -> Dict[str, Any]:
    """
    Fetches recent LinkedIn posts and activity for a profile.
    Useful for finding conversation starters, understanding interests, and personalization.
    Requires RAPIDAPI_KEY environment variable.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # RapidAPI implementation
    url = "https://linkedin-data-api.p.rapidapi.com/get-profile-posts"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "linkedin-data-api.p.rapidapi.com"
    }
    params = {"url": linkedin_url, "limit": limit}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": f"Failed to fetch activity: {str(e)}"}
