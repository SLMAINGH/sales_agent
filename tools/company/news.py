"""
Company news and research tools.
"""
import os
import requests
from typing import Any, Dict
from pydantic import BaseModel, Field
from langchain_core.tools import tool


class CompanyNewsInput(BaseModel):
    """Input for company news tool."""
    company_name: str = Field(description="Company name to search for")
    limit: int = Field(default=5, description="Number of news articles to fetch")


@tool("get_company_news", args_schema=CompanyNewsInput)
def get_company_news(company_name: str, limit: int = 5) -> Dict[str, Any]:
    """
    Fetches recent news articles about a company.
    Useful for finding timely conversation starters and understanding recent company developments.
    """
    # TODO: Implement with news API (e.g., NewsAPI, Bing News API)
    # Mock data for testing
    return {
        "articles": [
            {
                "title": f"{company_name} raises $50M Series B",
                "source": "TechCrunch",
                "date": "2024-01-20",
                "url": "https://techcrunch.com/...",
                "summary": "Leading AI startup announces major funding round..."
            },
            {
                "title": f"{company_name} launches new product",
                "source": "VentureBeat",
                "date": "2024-01-15",
                "url": "https://venturebeat.com/...",
                "summary": "Company unveils revolutionary AI-powered tool..."
            }
        ]
    }


class CompanyFundingInput(BaseModel):
    """Input for company funding tool."""
    company_name: str = Field(description="Company name to search for")


@tool("get_company_funding", args_schema=CompanyFundingInput)
def get_company_funding(company_name: str) -> Dict[str, Any]:
    """
    Fetches company funding information including total raised, investors, and funding rounds.
    Useful for understanding company stage and financial health.
    """
    # TODO: Implement with Crunchbase API or similar
    # Mock data for testing
    return {
        "total_funding": "$75M",
        "last_round": {
            "type": "Series B",
            "amount": "$50M",
            "date": "2024-01-20",
            "investors": ["Sequoia Capital", "Andreessen Horowitz"]
        },
        "previous_rounds": [
            {
                "type": "Series A",
                "amount": "$20M",
                "date": "2022-06-15"
            },
            {
                "type": "Seed",
                "amount": "$5M",
                "date": "2020-03-10"
            }
        ]
    }
