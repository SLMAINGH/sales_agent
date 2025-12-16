"""
LinkedIn profile scraping tool using RapidAPI.
"""
import os
import re
import requests
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool


def extract_username_from_url(linkedin_url: str) -> str:
    """Extract username from LinkedIn URL."""
    # Handle various LinkedIn URL formats:
    # https://linkedin.com/in/username
    # https://www.linkedin.com/in/username/
    # linkedin.com/in/username
    match = re.search(r'linkedin\.com/in/([^/?]+)', linkedin_url)
    if match:
        return match.group(1)
    return linkedin_url  # Fallback: assume it's already a username


class LinkedInProfileInput(BaseModel):
    """Input for LinkedIn profile tool."""
    linkedin_url: str = Field(description="LinkedIn profile URL to scrape")


@tool("get_linkedin_profile", args_schema=LinkedInProfileInput)
def get_linkedin_profile(linkedin_url: str) -> Dict[str, Any]:
    """
    Fetches LinkedIn profile data including name, headline, summary, experience, education, and skills.
    Useful for understanding a lead's background, career trajectory, and expertise.
    Uses Fresh LinkedIn Scraper API via RapidAPI.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # Extract username from URL
    username = extract_username_from_url(linkedin_url)

    # Fresh LinkedIn Scraper API
    url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/api/v1/user/profile"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "fresh-linkedin-scraper-api.p.rapidapi.com"
    }
    params = {"username": username}

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Return data as-is, let the qualifier/generator handle the structure
        if "error" in data or not data.get("success", True):
            return {"error": f"LinkedIn API error: {data.get('message', 'Unknown error')}"}

        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"LinkedIn API HTTP error {e.response.status_code}: {e.response.text[:200]}"}
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
    Uses Fresh LinkedIn Scraper API via RapidAPI.
    """
    api_key = os.getenv("RAPIDAPI_KEY")
    if not api_key:
        return {"error": "RAPIDAPI_KEY not configured. Set RAPIDAPI_KEY environment variable to enable LinkedIn scraping."}

    # Extract username from URL
    username = extract_username_from_url(linkedin_url)

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "fresh-linkedin-scraper-api.p.rapidapi.com"
    }

    try:
        # First, get the profile to extract the URN
        profile_url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/api/v1/user/profile"
        profile_response = requests.get(profile_url, headers=headers, params={"username": username}, timeout=30)
        profile_response.raise_for_status()
        profile_data = profile_response.json()

        if not profile_data.get("success") or "data" not in profile_data:
            return {"error": f"Could not get profile to extract URN: {profile_data.get('message', 'Unknown error')}"}

        urn = profile_data["data"].get("urn")
        if not urn:
            return {"error": "Profile does not contain URN"}

        # Now get posts using the URN
        posts_url = "https://fresh-linkedin-scraper-api.p.rapidapi.com/api/v1/user/posts"
        posts_response = requests.get(posts_url, headers=headers, params={"urn": urn, "page": 1}, timeout=30)
        posts_response.raise_for_status()
        data = posts_response.json()

        if "error" in data or not data.get("success", True):
            return {"error": f"LinkedIn API error: {data.get('message', 'Unknown error')}"}

        return data
    except requests.exceptions.HTTPError as e:
        return {"error": f"LinkedIn API HTTP error {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"Failed to fetch activity: {str(e)}"}
