# Customization Guide

Learn how to customize the sales qualification agent for your specific needs.

## Table of Contents

1. [Adjusting Campaign Context](#adjusting-campaign-context)
2. [Adding Custom Tools](#adding-custom-tools)
3. [Modifying Prompts](#modifying-prompts)
4. [Custom Qualification Logic](#custom-qualification-logic)
5. [Output Formats](#output-formats)
6. [Integrations](#integrations)

---

## Adjusting Campaign Context

The campaign context is the most important customization - it drives qualification and copy generation.

### Template

```python
CAMPAIGN_CONTEXT = """
[WHAT YOU'RE SELLING]

Target Profile:
- [WHO YOU'RE TARGETING]
- [COMPANY CHARACTERISTICS]
- [SPECIFIC CRITERIA]

Pain Points:
- [PROBLEM 1]
- [PROBLEM 2]
- [PROBLEM 3]

Value Proposition:
- [BENEFIT 1 with metric]
- [BENEFIT 2 with metric]
- [BENEFIT 3 with metric]

Pricing: [PRICING INFO]

Examples of Good Fit:
- [SCENARIO 1]
- [SCENARIO 2]
"""
```

### Real Examples

**Example 1: DevOps Tool**
```python
CAMPAIGN_CONTEXT = """
We're selling a Kubernetes cost optimization platform.

Target Profile:
- DevOps/Platform Engineers, Engineering Managers at tech companies
- Series A-D startups spending $20K+/month on cloud
- Using Kubernetes in production
- Pain points: Rising cloud costs, resource waste, poor visibility

Pain Points:
- Cloud bills growing faster than revenue
- Over-provisioned resources (30-60% waste typical)
- Lack of cost attribution by team/service
- Engineers don't know the cost impact of their decisions

Value Proposition:
- Reduce K8s costs by 40-60% on average
- Automated right-sizing recommendations
- Real-time cost dashboards with team attribution
- No code changes required

Pricing: $499/month per cluster (first cluster free trial)

Examples of Good Fit:
- Recently complained about cloud costs on LinkedIn
- Company is pre-profitability and watching burn rate
- Posted about K8s scaling challenges
- Engineering team > 20 people
"""
```

**Example 2: Sales Tool**
```python
CAMPAIGN_CONTEXT = """
We're selling an AI-powered sales email personalization tool.

Target Profile:
- Sales Leaders, RevOps, SDR Managers at B2B SaaS companies
- 50-500 employees, Series A-C stage
- Outbound sales motion with SDR team
- Pain points: Low reply rates, manual personalization doesn't scale

Pain Points:
- SDR reply rates < 5% on cold outreach
- Personalization is manual and time-consuming
- Can't scale quality outreach
- Burning leads with generic templates

Value Proposition:
- 3x reply rates with AI personalization
- Reduce SDR research time from 10min to 30sec per lead
- Write personalized emails at scale
- Integrates with Outreach, SalesLoft, HubSpot

Pricing: $199/user/month (minimum 5 seats)

Examples of Good Fit:
- Recently hired SDRs (growing team)
- Posted about improving cold email performance
- Using sales engagement platform (Outreach, SalesLoft)
- Targeting high-value accounts (ABM motion)
"""
```

### Tips for Effective Campaign Context

✅ **Be Specific:** "Series B SaaS" better than "tech company"
✅ **Include Metrics:** "3x reply rates" better than "better results"
✅ **Real Pain Points:** What they actually complain about
✅ **Buying Signals:** What indicates they're ready to buy
✅ **Disqualifiers:** Who is NOT a fit (saves money)

❌ **Too Broad:** "Any company" → Poor qualification
❌ **Too Narrow:** "Only Shopify engineers in NYC" → Miss good leads
❌ **Vague Benefits:** "Helps you work better" → Weak copy
❌ **No Context:** Just product features → No personalization

---

## Adding Custom Tools

Tools are the research capabilities of the agent.

### Tool Structure

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# 1. Define input schema
class MyToolInput(BaseModel):
    company_name: str = Field(description="Company to research")
    depth: str = Field(
        default="basic",
        description="Research depth: basic or detailed"
    )

# 2. Create tool with decorator
@tool("my_custom_tool", args_schema=MyToolInput)
def my_custom_tool(company_name: str, depth: str = "basic") -> dict:
    """
    Short description of what this tool does.
    The LLM uses this to decide when to call it.

    Useful for: [when to use this tool]
    """
    # Your implementation
    result = do_research(company_name, depth)
    return result

# 3. Register in tools/__init__.py
from tools.my_module import my_custom_tool

TOOLS = [
    # ... existing tools
    my_custom_tool,
]
```

### Example: Crunchbase Integration

**File: `tools/company/crunchbase.py`**

```python
import os
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class CrunchbaseInput(BaseModel):
    company_name: str = Field(description="Company name to lookup")

@tool("get_crunchbase_data", args_schema=CrunchbaseInput)
def get_crunchbase_data(company_name: str) -> dict:
    """
    Fetches company data from Crunchbase including funding, founders, investors.
    Useful for understanding company stage, financial health, and key people.
    """
    api_key = os.getenv("CRUNCHBASE_API_KEY")
    if not api_key:
        return {"error": "CRUNCHBASE_API_KEY not set"}

    # Crunchbase API call
    url = f"https://api.crunchbase.com/api/v4/entities/organizations/{company_name}"
    headers = {"X-cb-user-key": api_key}

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        return {
            "funding_total": data.get("funding_total", {}).get("value"),
            "last_funding_type": data.get("last_funding_type"),
            "num_employees": data.get("num_employees_enum"),
            "founded_on": data.get("founded_on"),
            "short_description": data.get("short_description"),
        }
    except Exception as e:
        return {"error": str(e)}
```

**Register in `tools/__init__.py`:**

```python
from tools.company.crunchbase import get_crunchbase_data

TOOLS = [
    get_linkedin_profile,
    get_linkedin_activity,
    # ... others
    get_crunchbase_data,  # Add here
]
```

That's it! The agent will now automatically use this tool when relevant.

### Example: GitHub Activity Tool

```python
# tools/tech/github.py
@tool("get_github_activity", args_schema=GitHubInput)
def get_github_activity(github_username: str) -> dict:
    """
    Fetches GitHub contribution activity and popular repositories.
    Useful for technical leads - shows their coding activity and interests.
    """
    url = f"https://api.github.com/users/{github_username}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "User not found"}

    data = response.json()
    return {
        "public_repos": data.get("public_repos"),
        "followers": data.get("followers"),
        "bio": data.get("bio"),
        "company": data.get("company"),
        "blog": data.get("blog"),
    }
```

### Tool Best Practices

✅ **Clear Description:** LLM decides when to use based on this
✅ **Descriptive Field Names:** `company_name` not `name`
✅ **Handle Errors:** Return `{"error": "..."}` instead of raising
✅ **Timeout Requests:** Set `timeout=30` on HTTP calls
✅ **Mock Data Fallback:** For testing without API keys
✅ **Rate Limiting:** Handle 429 errors gracefully

---

## Modifying Prompts

All system prompts are in `agent/prompts.py`.

### Qualification Prompt

**Location:** `agent/prompts.py:19`

**What it does:** Guides the LLM in scoring leads

**Customize to:**
- Change scoring criteria
- Adjust priority levels
- Add industry-specific factors

**Example: Adding Technical Depth Criterion**

```python
QUALIFICATION_SYSTEM_PROMPT = """You are a lead qualification expert for B2B sales.

Campaign Context:
{campaign_context}

Scoring guidelines:
- 90-100: Perfect fit - strong buy signals, technical depth, clear pain points
- 80-89: Excellent fit - matches ICP, recent relevant activity
- 60-79: Good fit - matches ICP, some relevant signals
- 40-59: Moderate fit - partial match, needs more research
- 0-39: Poor fit - missing key criteria or clear red flags

Consider:
1. **Job Title Match**: Does their role indicate buying power/influence?
2. **Company Fit**: Size, industry, stage, funding match target ICP?
3. **Timing Signals**: Recent job change, company fundraise, posted about relevant topics?
4. **Engagement Potential**: Active on LinkedIn, thought leader, responds to outreach?
5. **Technical Depth** [NEW]: For technical products, do they have hands-on experience?

For technical products:
- Bonus points for: GitHub activity, conference talks, technical blog posts
- Red flag: No hands-on experience with relevant technology

Provide:
- Qualification score (0-100)
- Specific reasons they're a good fit
- Any red flags or concerns
- Actionable insights for personalization
- Priority level (high/medium/low)"""
```

### Copy Generation Prompt

**Location:** `agent/prompts.py:54`

**What it does:** Guides the LLM in writing personalized copy

**Customize to:**
- Change tone (formal vs casual)
- Adjust length
- Add specific requirements

**Example: More Aggressive CTA**

```python
COPY_GENERATION_SYSTEM_PROMPT = """You are an expert B2B sales copywriter.

Campaign Context:
{campaign_context}

Copywriting principles:
1. **Lead with Value**: Start with what's in it for them
2. **Show You Did Research**: Reference specific, recent activity
3. **Keep It Short**: 2-3 short paragraphs max for email
4. **Natural Tone**: Conversational, not salesy
5. **Strong CTA**: Be direct and specific about next step [MODIFIED]

For LinkedIn messages:
- 3-4 sentences only
- Casual but professional tone
- End with specific ask: "Open to a 15-min call this week?"

For email:
- Subject line that stands out
- Brief intro showing you know them
- Value prop tied to their situation
- Clear, direct CTA: "Can we schedule 15 minutes this Thursday or Friday?" [MODIFIED]

Talking points:
- Discovery questions to uncover pain
- Specific questions about their current setup
- Value props relevant to their situation

IMPORTANT: Always end with a specific time ask, not "let me know if interested"."""
```

---

## Custom Qualification Logic

Want to add custom scoring logic beyond LLM analysis?

### Example: Boost Score for Recent Job Changes

**File:** `agent/lead_qualifier.py:16`

**Add after LLM call:**

```python
async def qualify_lead(
    self,
    lead: Lead,
    profile_data: Dict[str, Any],
    company_data: Dict[str, Any],
) -> LeadQualification:
    # ... existing LLM call ...
    qualification = await call_llm(...)

    # Custom logic: Boost for recent job change
    if self._is_recent_job_change(profile_data):
        original_score = qualification.score
        qualification.score = min(100, qualification.score + 10)
        qualification.key_insights.append(
            f"Recently started role (boosted score from {original_score})"
        )

    return qualification

def _is_recent_job_change(self, profile_data: Dict[str, Any]) -> bool:
    """Check if person started current job in last 90 days"""
    profile = profile_data.get("get_linkedin_profile", {})
    if not isinstance(profile, dict):
        return False

    experience = profile.get("experience", [])
    if not experience:
        return False

    current_job = experience[0]
    duration = current_job.get("duration", "")

    # Simple heuristic: contains "months" and number < 3
    if "month" in duration.lower():
        # Extract number (e.g., "2 months" -> 2)
        import re
        match = re.search(r'(\d+)', duration)
        if match and int(match.group(1)) <= 3:
            return True

    return False
```

### Example: Disqualify Based on Company Size

```python
async def qualify_lead(...) -> LeadQualification:
    qualification = await call_llm(...)

    # Auto-disqualify if company too small
    company_size = self._extract_company_size(company_data)
    if company_size and company_size < 10:
        qualification.score = max(0, qualification.score - 40)
        qualification.red_flags.append(
            "Company size below minimum threshold (< 10 employees)"
        )
        qualification.priority = "low"

    return qualification

def _extract_company_size(self, company_data: Dict[str, Any]) -> Optional[int]:
    company = company_data.get("get_linkedin_company", {})
    size_str = company.get("company_size", "")

    # Parse "51-200 employees" -> 125 (midpoint)
    if "-" in size_str:
        parts = size_str.split("-")
        try:
            low = int(parts[0])
            high = int(parts[1].split()[0])
            return (low + high) // 2
        except:
            return None
    return None
```

---

## Output Formats

### Adding a New Export Format

**Example: Export to Notion**

**File:** `main.py` (add function)

```python
def save_results_to_notion(qualified_leads, notion_database_id: str):
    """Save results to Notion database."""
    from notion_client import Client

    notion = Client(auth=os.getenv("NOTION_API_KEY"))

    for ql in qualified_leads:
        # Only add high-priority leads
        if ql.qualification.priority != "high":
            continue

        notion.pages.create(
            parent={"database_id": notion_database_id},
            properties={
                "Name": {"title": [{"text": {"content": ql.lead.name}}]},
                "Company": {"rich_text": [{"text": {"content": ql.lead.company_name}}]},
                "Score": {"number": ql.qualification.score},
                "LinkedIn": {"url": ql.lead.linkedin_url},
            },
            children=[
                {
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {"rich_text": [{"type": "text", "text": {"content": "LinkedIn Message"}}]}
                },
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"type": "text", "text": {"content": ql.personalized_copy.linkedin_message}}]}
                }
            ]
        )

    print(f"✓ Saved {len([q for q in qualified_leads if q.qualification.priority == 'high'])} high-priority leads to Notion")
```

**Usage:**
```python
# In main()
save_results_to_notion(qualified_leads, "your-notion-database-id")
```

### Export to HubSpot

```python
def save_results_to_hubspot(qualified_leads):
    """Create contacts in HubSpot with custom properties."""
    import hubspot
    from hubspot.crm.contacts import SimplePublicObjectInputForCreate

    client = hubspot.Client.create(access_token=os.getenv("HUBSPOT_API_KEY"))

    for ql in qualified_leads:
        if ql.qualification.score < 60:
            continue  # Only import qualified leads

        contact = SimplePublicObjectInputForCreate(
            properties={
                "firstname": ql.lead.name.split()[0],
                "lastname": " ".join(ql.lead.name.split()[1:]),
                "email": "",  # Would need to enrich
                "company": ql.lead.company_name,
                "jobtitle": ql.lead.title,
                "linkedin_url": ql.lead.linkedin_url,
                "hs_lead_status": "NEW",
                "qualification_score": str(ql.qualification.score),
                "personalized_message": ql.personalized_copy.linkedin_message if ql.personalized_copy else "",
            }
        )

        try:
            client.crm.contacts.basic_api.create(simple_public_object_input_for_create=contact)
        except Exception as e:
            print(f"Failed to create contact for {ql.lead.name}: {e}")

    print(f"✓ Created contacts in HubSpot")
```

---

## Integrations

### Sales Navigator CSV Import

**Format:** Export from Sales Navigator and add an `id` column

```python
def load_from_sales_navigator_export(csv_path: str) -> List[Lead]:
    """Load leads from Sales Navigator export CSV."""
    import csv
    import hashlib

    leads = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # Sales Navigator exports use different column names
            linkedin_url = row.get('Profile URL', '')
            name = f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip()

            # Generate ID from LinkedIn URL
            lead_id = hashlib.md5(linkedin_url.encode()).hexdigest()[:12]

            leads.append(Lead(
                id=lead_id,
                name=name,
                linkedin_url=linkedin_url,
                company_name=row.get('Company', ''),
                title=row.get('Title', ''),
                sales_navigator_data=dict(row),  # Store full export data
            ))

    return leads
```

### Enrichment APIs (Clearbit, Apollo, etc.)

```python
# tools/enrichment/clearbit.py
@tool("enrich_with_clearbit", args_schema=ClearbitInput)
def enrich_with_clearbit(linkedin_url: str) -> dict:
    """
    Enriches lead data with Clearbit (email, phone, etc.).
    Useful for finding contact information.
    """
    import clearbit
    clearbit.key = os.getenv("CLEARBIT_API_KEY")

    try:
        person = clearbit.Person.find(linkedin=linkedin_url)
        return {
            "email": person.get("email"),
            "phone": person.get("phone"),
            "employment": person.get("employment", {}).get("role"),
        }
    except:
        return {"error": "Not found"}
```

### Slack Notifications

```python
def send_slack_notification(qualified_leads):
    """Send Slack message with high-priority leads."""
    import requests

    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    high_priority = [q for q in qualified_leads if q.qualification.priority == "high"]

    if not high_priority:
        return

    message = {
        "text": f"🎯 {len(high_priority)} new high-priority leads!",
        "blocks": [
            {"type": "header", "text": {"type": "plain_text", "text": f"🎯 {len(high_priority)} High-Priority Leads"}},
        ]
    }

    for ql in high_priority[:5]:  # Top 5
        message["blocks"].append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*{ql.lead.name}* ({ql.qualification.score}/100)\n{ql.lead.title} at {ql.lead.company_name}\n<{ql.lead.linkedin_url}|View Profile>"}
        })

    requests.post(webhook_url, json=message)
```

---

## Advanced Customizations

### Multi-Tenant Support

Run different campaigns simultaneously:

```python
campaigns = {
    "enterprise": ENTERPRISE_CAMPAIGN_CONTEXT,
    "smb": SMB_CAMPAIGN_CONTEXT,
}

for campaign_name, context in campaigns.items():
    agent = SalesQualificationAgent(
        campaign_context=context,
        context_dir=f".leads/context_{campaign_name}"
    )
    results = await agent.process_leads(leads_for_campaign[campaign_name])
    save_results(results, f"output/{campaign_name}_leads.json")
```

### A/B Testing Copy

```python
# Generate multiple copy variants
copy_variants = []
for temperature in [0.7, 0.9, 1.1]:
    copy = await generate_copy_with_temperature(lead, temperature)
    copy_variants.append(copy)

# Pick best based on criteria
best_copy = select_best_copy(copy_variants, criteria="clarity")
```

See the code for more ideas!
