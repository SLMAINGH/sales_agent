"""
Pydantic schemas for the sales qualification agent.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class Lead(BaseModel):
    """Input lead from Sales Navigator."""
    id: str = Field(description="Unique identifier for the lead")
    name: str = Field(description="Full name of the lead")
    linkedin_url: str = Field(description="LinkedIn profile URL")
    company_name: str = Field(description="Company name")
    title: str = Field(description="Job title")
    sales_navigator_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Raw data from Sales Navigator"
    )


class SubTask(BaseModel):
    """A single subtask within a planned task."""
    id: int = Field(description="Unique identifier for the subtask")
    description: str = Field(description="What data to fetch or action to perform")


class PlannedTask(BaseModel):
    """A planned research task with subtasks."""
    id: int = Field(description="Unique identifier for the task")
    type: Literal["company_research", "profile_research"] = Field(
        description="Type of research task"
    )
    description: str = Field(description="High-level description of the task")
    company: Optional[str] = Field(default=None, description="Company being researched")
    lead_id: Optional[str] = Field(default=None, description="Lead ID for profile research")
    lead_ids: Optional[List[str]] = Field(
        default=None, description="Lead IDs associated with company research"
    )
    sub_tasks: List[SubTask] = Field(description="Subtasks to execute")


class ResearchPlan(BaseModel):
    """Complete research plan for a batch of leads."""
    tasks: List[PlannedTask] = Field(description="All planned research tasks")


class LeadQualification(BaseModel):
    """Qualification result for a lead."""
    score: int = Field(ge=0, le=100, description="Qualification score from 0-100")
    fit_reasons: List[str] = Field(description="Reasons this lead is a good fit")
    red_flags: List[str] = Field(description="Concerns or red flags about this lead")
    key_insights: List[str] = Field(description="Specific insights for personalization")
    priority: Literal["high", "medium", "low"] = Field(description="Priority level")


class PersonalizedCopy(BaseModel):
    """Personalized outreach copy for a lead."""
    subject_line: str = Field(description="Email subject line")
    email_body: str = Field(description="Full email body")
    linkedin_message: str = Field(description="LinkedIn connection/InMail message")
    talking_points: List[str] = Field(description="Key talking points for calls/meetings")


class ResearchSummary(BaseModel):
    """Summary of research data collected."""
    profile_highlights: List[str] = Field(description="Key profile highlights")
    company_highlights: List[str] = Field(description="Key company highlights")
    recent_activity: List[str] = Field(description="Notable recent activity")


class QualifiedLead(BaseModel):
    """Complete output for a qualified lead."""
    lead: Lead
    qualification: LeadQualification
    personalized_copy: Optional[PersonalizedCopy] = Field(
        default=None, description="Copy (only generated if score meets threshold)"
    )
    research_summary: ResearchSummary


class SelectedContexts(BaseModel):
    """LLM output for selecting relevant contexts."""
    context_ids: List[int] = Field(description="List of relevant context IDs (0-indexed)")
