"""
Company research tools using Perplexity AI.
"""
import os
import requests
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CompanyResearchInput(BaseModel):
    """Input for company research tool."""
    company_name: str = Field(description="Company name to research")


@tool("research_company", args_schema=CompanyResearchInput)
def research_company(company_name: str) -> Dict[str, Any]:
    """
    Research a company using Perplexity AI to find recent news, funding, products, and key developments.
    Useful for understanding company context, recent events, and finding personalization hooks.
    """
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return {"error": "PERPLEXITY_API_KEY not configured. Set PERPLEXITY_API_KEY environment variable."}

    url = "https://api.perplexity.ai/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Craft a research query for Perplexity
    query = f"""Research {company_name} company and provide:
1. Recent news and announcements (last 3 months)
2. Funding history and investors
3. Main products/services
4. Company size and growth
5. Key executive changes or hires
6. Any recent product launches or partnerships

Focus on information that would be useful for personalized sales outreach."""

    payload = {
        "model": "llama-3.1-sonar-small-128k-online",
        "messages": [
            {
                "role": "system",
                "content": "You are a business research assistant. Provide concise, factual information about companies for sales intelligence purposes."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.2,
        "return_citations": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Extract the research content
        if "choices" in data and len(data["choices"]) > 0:
            research_text = data["choices"][0]["message"]["content"]
            citations = data.get("citations", [])

            return {
                "company_name": company_name,
                "research": research_text,
                "citations": citations,
                "success": True
            }
        else:
            return {"error": "No research results from Perplexity API"}

    except requests.exceptions.HTTPError as e:
        return {"error": f"Perplexity API HTTP error {e.response.status_code}: {e.response.text[:200]}"}
    except Exception as e:
        return {"error": f"Failed to research company: {str(e)}"}
