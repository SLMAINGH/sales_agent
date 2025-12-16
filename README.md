# Sales Lead Qualifier 🎯

An AI-powered sales qualification agent that researches LinkedIn profiles, qualifies leads, and generates personalized outreach copy. Built using the Dexter agent architecture pattern.

## Features

✨ **Intelligent Research Planning**
- Automatically deduplicates company research when multiple leads work at the same company
- Creates optimized research plans with parallel execution

🔍 **Comprehensive Lead Research**
- LinkedIn profile scraping (via RapidAPI)
- Recent activity and posts analysis
- Company data and news aggregation
- Funding information

🎯 **Smart Qualification**
- AI-powered scoring (0-100)
- Priority assignment (high/medium/low)
- Fit analysis with specific reasons
- Red flag detection

✍️ **Personalized Copy Generation**
- Context-aware email subject lines
- Personalized email body (2-3 paragraphs)
- LinkedIn connection messages
- Talking points for calls

## Architecture

Based on the Dexter agent architecture with four phases:

1. **Planning Phase** (`LeadPlanner`)
   - Groups leads by company
   - Creates company research tasks (deduplicated)
   - Creates individual profile research tasks

2. **Execution Phase** (`LeadExecutor`)
   - Resolves subtasks to tool calls via LLM
   - Executes research tools in parallel
   - Saves results to filesystem

3. **Qualification Phase** (`LeadQualifier`)
   - Analyzes profile + company data
   - Generates qualification score and insights

4. **Copy Generation Phase** (`CopyGenerator`)
   - Creates personalized outreach copy
   - Only for leads meeting qualification threshold

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd sales-qualifier
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Usage

### Quick Start

Run the example with mock data:

```bash
python main.py
```

### Using Your Own Leads

**Option 1: Modify main.py**

```python
leads = [
    Lead(
        id="lead_1",
        name="John Smith",
        linkedin_url="https://linkedin.com/in/johnsmith",
        company_name="TechCorp",
        title="VP of Engineering"
    ),
    # ... more leads
]
```

**Option 2: Load from CSV**

Create a CSV file with columns: `id`, `name`, `linkedin_url`, `company_name`, `title`

```python
leads = load_leads_from_csv('my_leads.csv')
```

### Customize Campaign Context

Edit the `CAMPAIGN_CONTEXT` in `main.py` to match your product/service:

```python
CAMPAIGN_CONTEXT = """
We're selling [your product].

Target Profile:
- [job titles] at [company types]
- Company size: [range]
- Pain points: [list]

Value Proposition:
- [benefit 1]
- [benefit 2]

Pricing: [pricing info]
"""
```

## Output

The agent generates two files in the `output/` directory:

1. **qualified_leads.json** - Full detailed results
2. **qualified_leads.csv** - Simplified spreadsheet format

Example output structure:

```json
{
  "lead": {
    "name": "John Smith",
    "title": "VP of Engineering",
    "company": "TechCorp"
  },
  "qualification": {
    "score": 85,
    "priority": "high",
    "fit_reasons": ["Strong technical background", "Company in growth phase"],
    "key_insights": ["Recently posted about code quality"]
  },
  "personalized_copy": {
    "subject_line": "Thoughts on your recent post about code reviews",
    "linkedin_message": "Hi John, loved your recent post about...",
    "email_body": "...",
    "talking_points": ["..."]
  }
}
```

## Project Structure

```
sales-qualifier/
├── agent/
│   ├── schemas.py              # Pydantic models
│   ├── prompts.py              # System prompts
│   ├── lead_planner.py         # Research planning with deduplication
│   ├── lead_executor.py        # Tool execution
│   ├── lead_qualifier.py       # Lead scoring
│   ├── copy_generator.py       # Personalized copy
│   └── sales_agent.py          # Main orchestrator
├── tools/
│   ├── linkedin/
│   │   ├── profile.py          # Profile scraping
│   │   └── company.py          # Company scraping
│   └── company/
│       └── news.py             # News & funding tools
├── utils/
│   └── context.py              # Tool context manager
├── model/
│   └── llm.py                  # LLM interface
├── main.py                     # Entry point
├── requirements.txt
└── README.md
```

## Configuration

### Models

- **Planning & Qualification**: `gpt-4o-mini` (fast and cheap)
- **Copy Generation**: `gpt-4o` (better quality)

Change models in `main.py`:

```python
agent = SalesQualificationAgent(
    campaign_context=CAMPAIGN_CONTEXT,
    model="gpt-4o-mini",
    copy_model="gpt-4o",
    qualification_threshold=50,
)
```

### Qualification Threshold

Only leads scoring above this threshold get personalized copy generated:

```python
qualification_threshold=50  # 0-100
```

## API Keys

### OpenAI (Required)

Get your API key at https://platform.openai.com/api-keys

### RapidAPI (Optional)

For real LinkedIn scraping, get a RapidAPI key:
1. Sign up at https://rapidapi.com
2. Subscribe to a LinkedIn scraping API (e.g., "LinkedIn Data API")
3. Add `RAPIDAPI_KEY` to your `.env` file

**Note**: Without RapidAPI key, the system uses mock data for testing.

## Advanced Usage

### Adding Custom Tools

Create a new tool in `tools/`:

```python
from pydantic import BaseModel, Field
from langchain_core.tools import tool

class MyToolInput(BaseModel):
    param: str = Field(description="...")

@tool("my_tool", args_schema=MyToolInput)
def my_tool(param: str) -> dict:
    """Tool description for the LLM."""
    # Implementation
    return {"result": "..."}
```

Register in `tools/__init__.py`:

```python
from tools.mytool import my_tool

TOOLS = [
    # ... existing tools
    my_tool,
]
```

### Batch Processing

Process large lists of leads in batches:

```python
batch_size = 10
for i in range(0, len(all_leads), batch_size):
    batch = all_leads[i:i+batch_size]
    qualified = await agent.process_leads(batch)
    # Save results for this batch
```

## Limitations

- **Rate Limits**: Be mindful of API rate limits (OpenAI, RapidAPI)
- **Cost**: Using GPT-4 for all leads can be expensive
- **LinkedIn TOS**: Check LinkedIn's terms before scraping at scale
- **Mock Data**: Tools use mock data without RapidAPI key

## Contributing

Contributions welcome! Areas for improvement:

- Additional data sources (Crunchbase, company websites)
- CRM integrations (HubSpot, Salesforce)
- Email sending integration
- A/B testing framework for copy
- Multi-language support

## License

MIT License

## Documentation

Comprehensive guides available in `/docs`:

- **[Getting Started](./docs/GETTING_STARTED.md)** - Installation, first run, basic usage
- **[Architecture Guide](./docs/ARCHITECTURE.md)** - How it works under the hood
- **[Customization Guide](./docs/CUSTOMIZATION.md)** - Add tools, modify behavior, integrations
- **[Best Practices](./docs/BEST_PRACTICES.md)** - Tips for effective lead qualification
- **[FAQ](./docs/FAQ.md)** - Common questions and troubleshooting

## Acknowledgments

Architecture inspired by [Dexter](https://github.com/virattt/dexter) by @virattt
