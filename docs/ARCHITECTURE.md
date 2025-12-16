# Architecture Guide

This agent is built using the **Dexter architecture pattern** - a multi-agent pipeline optimized for research and analysis tasks.

## High-Level Overview

```
User Input (Leads + Campaign Context)
         ↓
    [LeadPlanner] ← LLM: Creates research plan
         ↓
  [LeadExecutor] ← LLM: Resolves tasks to tool calls
         ↓
  [ToolContextManager] → Saves results to .leads/context/
         ↓
  [LeadQualifier] ← LLM: Analyzes fit (0-100 score)
         ↓
  [CopyGenerator] ← LLM: Creates personalized copy
         ↓
    Output (QualifiedLead objects)
```

---

## Four-Phase Pipeline

### Phase 1: Planning (LeadPlanner)

**Purpose:** Create an optimized research plan with company deduplication

**Input:**
- List of `Lead` objects
- Campaign context string

**Process:**
1. Group leads by company name
2. Send to LLM with tool schemas
3. LLM creates:
   - One `company_research` task per unique company
   - One `profile_research` task per lead

**Output:** `ResearchPlan` with list of `PlannedTask` objects

**Example:**
```python
# Input: 3 leads (2 from TechCorp, 1 from StartupXYZ)
# Output:
ResearchPlan(tasks=[
    PlannedTask(
        id=1,
        type="company_research",
        company="TechCorp",
        lead_ids=["lead_1", "lead_2"],  # Shared research!
        sub_tasks=[
            SubTask(id=1, description="Get LinkedIn company page for TechCorp"),
            SubTask(id=2, description="Get recent company posts"),
            SubTask(id=3, description="Get company news"),
        ]
    ),
    PlannedTask(
        id=2,
        type="profile_research",
        lead_id="lead_1",
        sub_tasks=[
            SubTask(id=1, description="Get LinkedIn profile for lead_1"),
            SubTask(id=2, description="Get recent activity"),
        ]
    ),
    # ... more tasks
])
```

**Key Files:**
- `agent/lead_planner.py:28` - Main planning logic
- `agent/prompts.py:8` - Planning system prompt
- `agent/schemas.py:29` - PlannedTask schema

**Fallback:** If LLM fails, creates a basic plan manually

---

### Phase 2: Execution (LeadExecutor)

**Purpose:** Execute research tasks and save results

**Input:** `ResearchPlan` from Phase 1

**Process:**
1. For each task (in parallel):
   - Send subtasks to LLM with tool bindings
   - LLM returns tool calls (name + args)
   - Execute tools (in parallel)
   - Save results via `ToolContextManager`

**Example Flow:**
```python
# Subtask: "Get LinkedIn profile for John Smith"
# ↓ LLM resolves to:
tool_call = {
    "name": "get_linkedin_profile",
    "args": {"linkedin_url": "https://linkedin.com/in/johnsmith"}
}
# ↓ Execute tool:
result = get_linkedin_profile("https://linkedin.com/in/johnsmith")
# ↓ Save to disk:
context_manager.save_context(
    tool_name="get_linkedin_profile",
    args={"linkedin_url": "..."},
    result=result,
    lead_id="lead_1"
)
```

**Output:** Tool results saved to `.leads/context/*.json`

**Key Files:**
- `agent/lead_executor.py:36` - Execution engine
- `utils/context.py:116` - Context saving
- `tools/*.py` - Individual tools

**Parallelization:**
- All tasks execute in parallel (`asyncio.gather`)
- All tool calls within a task execute in parallel

---

### Phase 3: Qualification (LeadQualifier)

**Purpose:** Analyze each lead and assign a qualification score

**Input:**
- `Lead` object
- Profile data (aggregated from context manager)
- Company data (aggregated from context manager)
- Campaign context

**Process:**
1. Load research data for this lead
2. Format data into a prompt
3. Send to LLM with structured output schema
4. LLM returns `LeadQualification` object

**LLM Prompt Structure:**
```
System: You are a lead qualification expert...

User:
Lead: John Smith - VP of Engineering at TechCorp

Profile Data:
- Headline: VP of Engineering at TechCorp
- Recent posts: "Struggling with code review bottlenecks..."
- Skills: Python, Engineering Leadership, System Design

Company Data:
- Size: 51-200 employees
- Recent funding: Series B, $50M
- Industry: Software Development

Campaign Context:
We're selling an AI code review tool targeting VPs at Series A-C...

Analyze and return: score, fit_reasons, red_flags, insights, priority
```

**Output:**
```python
LeadQualification(
    score=85,
    priority="high",
    fit_reasons=[
        "Senior technical leadership with budget authority",
        "Company size matches ICP (50-200 employees)",
        "Recently posted about code review challenges"
    ],
    red_flags=[],
    key_insights=[
        "Mentioned team growing rapidly",
        "Posted about scaling challenges"
    ]
)
```

**Key Files:**
- `agent/lead_qualifier.py:16` - Qualification logic
- `agent/prompts.py:19` - Qualification system prompt
- `agent/schemas.py:44` - LeadQualification schema

---

### Phase 4: Copy Generation (CopyGenerator)

**Purpose:** Create personalized outreach copy

**Input:**
- `Lead` object
- `LeadQualification` from Phase 3
- Profile & company data
- Campaign context

**Process:**
1. Extract personalization hooks (recent posts, company news)
2. Build prompt with lead context + qualification insights
3. Send to LLM (using better model: gpt-4o)
4. LLM returns `PersonalizedCopy` object

**Only Runs If:** `qualification.score >= threshold` (default: 50)

**LLM Prompt Structure:**
```
System: You are an expert B2B sales copywriter...

User:
Lead: John Smith - VP of Engineering at TechCorp
Score: 85/100 (high priority)
Key Insights: Posted about code review bottlenecks, team scaling

Recent Activity:
- "Our team grew from 10 to 50 engineers in 6 months..."
- "Code review is becoming a bottleneck..."

Company News:
- TechCorp raises $50M Series B (Jan 2024)
- TechCorp launches new AI product

Generate personalized outreach copy:
1. Subject line (reference recent activity)
2. Email body (2-3 paragraphs, value-focused)
3. LinkedIn message (3-4 sentences, casual)
4. Talking points for calls
```

**Output:**
```python
PersonalizedCopy(
    subject_line="Re: Your post on code review at scale",
    linkedin_message="Hi John, loved your post about scaling code reviews...",
    email_body="Hi John,\n\nI saw your recent post...",
    talking_points=[
        "Ask about their current review process",
        "Share case study from similar Series B company"
    ]
)
```

**Key Files:**
- `agent/copy_generator.py:16` - Copy generation logic
- `agent/prompts.py:54` - Copy generation system prompt
- `agent/schemas.py:51` - PersonalizedCopy schema

---

## Supporting Components

### ToolContextManager

**Purpose:** Manage tool output persistence and retrieval

**Key Methods:**

```python
# Save tool output to filesystem
save_context(
    tool_name="get_linkedin_profile",
    args={"linkedin_url": "..."},
    result={...},
    lead_id="lead_1",
    company="TechCorp"
)
# → Saves to: .leads/context/lead_1_get_linkedin_profile_abc123.json

# Get all contexts for a lead
profile_data = get_context_for_lead("lead_1")
# → Returns: {"get_linkedin_profile": {...}, "get_linkedin_activity": {...}}

# Get all contexts for a company
company_data = get_context_for_company("TechCorp")
# → Returns: {"get_linkedin_company": {...}, "get_company_news": {...}}
```

**Why Filesystem Storage?**
- Memory efficient (don't hold all data in RAM)
- Persistent (can resume if interrupted)
- Debuggable (can inspect .json files manually)
- Cacheable (reuse data across runs)

**File Naming:**
```
{identifier}_{tool_name}_{args_hash}.json

Examples:
- lead_1_get_linkedin_profile_a1b2c3.json
- TechCorp_get_linkedin_company_d4e5f6.json
```

**Key Files:**
- `utils/context.py:28` - ToolContextManager class

---

### Tools

**Structure:**
All tools use LangChain's `@tool` decorator with Pydantic schemas.

**Example:**
```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class LinkedInProfileInput(BaseModel):
    linkedin_url: str = Field(description="LinkedIn profile URL")

@tool("get_linkedin_profile", args_schema=LinkedInProfileInput)
def get_linkedin_profile(linkedin_url: str) -> dict:
    """
    Fetches LinkedIn profile data including experience, education, skills.
    Useful for understanding a lead's background and expertise.
    """
    # Implementation (RapidAPI call or mock data)
    return {...}
```

**Available Tools:**
1. `get_linkedin_profile` - Profile data
2. `get_linkedin_activity` - Recent posts
3. `get_linkedin_company` - Company page
4. `get_company_posts` - Company updates
5. `get_company_news` - News articles
6. `get_company_funding` - Funding info

**Adding New Tools:**
See [CUSTOMIZATION.md](./CUSTOMIZATION.md#adding-tools)

**Key Files:**
- `tools/linkedin/profile.py` - LinkedIn profile tools
- `tools/linkedin/company.py` - LinkedIn company tools
- `tools/company/news.py` - Company research tools
- `tools/__init__.py` - Tool registry

---

### LLM Interface

**Purpose:** Unified interface for LLM calls

**Supports:**
- Structured output (Pydantic schemas)
- Tool binding (function calling)
- Streaming responses
- Multiple providers (OpenAI, Anthropic, Google)

**Key Functions:**

```python
# Structured output
result = await call_llm(
    prompt="...",
    system_prompt="...",
    output_schema=LeadQualification,  # Pydantic model
    model="gpt-4o-mini"
)
# → Returns: LeadQualification object

# Tool binding
result = await call_llm(
    prompt="...",
    tools=[get_linkedin_profile, get_company_news],
    model="gpt-4o-mini"
)
# → Returns: AIMessage with tool_calls

# Streaming
async for chunk in call_llm_stream(
    prompt="...",
    model="gpt-4o"
):
    print(chunk, end="")
```

**Key Files:**
- `model/llm.py:15` - LLM interface

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────┐
│ User Input                                              │
│ - leads: List[Lead]                                     │
│ - campaign_context: str                                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 1: LeadPlanner                                    │
│ - Groups leads by company                               │
│ - Creates ResearchPlan with deduplication              │
│   • company_research tasks (1 per company)              │
│   • profile_research tasks (1 per lead)                 │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 2: LeadExecutor                                   │
│ - Resolves subtasks → tool calls (via LLM)             │
│ - Executes tools in parallel                            │
│ - Saves results to ToolContextManager                   │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ ToolContextManager                                      │
│ - Saves: .leads/context/{lead_id}_{tool}_{hash}.json   │
│ - Provides: get_context_for_lead(lead_id)              │
│ - Provides: get_context_for_company(company)            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3: LeadQualifier (parallel per lead)             │
│ - Loads: profile_data + company_data                    │
│ - Analyzes fit via LLM                                  │
│ - Returns: LeadQualification (score, priority, etc.)    │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 4: CopyGenerator (if score >= threshold)         │
│ - Extracts personalization hooks                        │
│ - Generates copy via LLM                                │
│ - Returns: PersonalizedCopy (LinkedIn msg, email, etc.) │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│ Output                                                  │
│ - qualified_leads: List[QualifiedLead]                  │
│ - Saved to: output/qualified_leads.json                 │
│ - Saved to: output/qualified_leads.csv                  │
└─────────────────────────────────────────────────────────┘
```

---

## Key Design Patterns

### 1. Two-Pass Architecture

**Problem:** How to plan research without knowing exact tool calls?

**Solution:** Separate planning from execution
- **Pass 1 (Planning):** Create task *descriptions* ("Get LinkedIn profile for John")
- **Pass 2 (Execution):** Resolve descriptions to *tool calls* (get_linkedin_profile with args)

**Benefits:**
- More flexible planning (LLM can create creative research strategies)
- Better error handling (can retry tool resolution without replanning)
- Clearer separation of concerns

### 2. Company Deduplication

**Problem:** Wasteful to research same company multiple times

**Solution:** Group leads by company in planning phase
- Single company_research task with multiple `lead_ids`
- Results saved with `company="TechCorp"` (shared)
- All leads from TechCorp reference same company data

**Benefits:**
- Faster execution (fewer API calls)
- Cost savings (fewer LLM calls)
- Consistent company data across leads

### 3. Lazy Loading

**Problem:** Loading all tool outputs into memory is wasteful

**Solution:** Filesystem-based context management
- Save outputs immediately after execution
- Only load contexts when needed (per-lead basis)
- Use "pointers" (lightweight metadata) instead of full data

**Benefits:**
- Memory efficient (scales to thousands of leads)
- Faster startup (no loading upfront)
- Can resume interrupted runs

### 4. Structured Output with Pydantic

**Problem:** LLM outputs are unpredictable strings

**Solution:** Use Pydantic schemas with LangChain's structured output
- Define exact schema (fields, types, descriptions)
- LLM returns valid JSON matching schema
- Automatic validation and type coercion

**Benefits:**
- Type-safe throughout codebase
- Clear contracts between components
- Auto-complete in IDEs

### 5. Graceful Degradation

**Problem:** External services (LLM, APIs) can fail

**Solution:** Fallbacks at every level
- Planning fails → Manual fallback plan
- Tool resolution fails → Skip task, continue
- Qualification fails → Return default low score
- Copy generation fails → Return generic template

**Benefits:**
- System never fully crashes
- Partial results better than no results
- Easy to identify which components failed

---

## Performance Characteristics

### Parallelization

**Task Level:**
```python
# All tasks run in parallel
await asyncio.gather(*[
    execute_task(task1),  # Company research
    execute_task(task2),  # Profile research
    execute_task(task3),  # Profile research
])
```

**Tool Level:**
```python
# All tools within a task run in parallel
await asyncio.gather(*[
    execute_tool("get_linkedin_profile"),
    execute_tool("get_linkedin_activity"),
])
```

**Lead Level:**
```python
# All leads qualified/copied in parallel
await asyncio.gather(*[
    process_lead(lead1),
    process_lead(lead2),
    process_lead(lead3),
])
```

### Time Complexity

For N leads from C companies:

1. **Planning:** O(1) - Single LLM call
2. **Execution:** O(C + N) - Parallel tasks
3. **Qualification:** O(N) - Parallel per lead
4. **Copy Generation:** O(N) - Parallel per lead

**Total: O(N) with company deduplication**

Without deduplication: O(N * tools_per_company)

### Cost Estimate

Per lead (with defaults):
- Planning: ~500 tokens × $0.00015 = $0.00008
- Execution (tool resolution): ~500 tokens × $0.00015 = $0.00008
- Qualification: ~1000 tokens × $0.00015 = $0.00015
- Copy generation: ~1500 tokens × $0.0025 = $0.00375

**Total: ~$0.006 per lead** (with company deduplication)

---

## Extension Points

Want to customize? These are the main extension points:

1. **Add Tools:** Create new tools in `tools/`
2. **Custom Prompts:** Edit `agent/prompts.py`
3. **New Schemas:** Add fields to `agent/schemas.py`
4. **Different LLM:** Modify `model/llm.py`
5. **Post-Processing:** Add logic to `agent/sales_agent.py`

See [CUSTOMIZATION.md](./CUSTOMIZATION.md) for details.
