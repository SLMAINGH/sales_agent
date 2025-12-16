# Getting Started with Sales Lead Qualifier

## Quick Start (5 minutes)

### 1. Installation

```bash
cd sales-qualifier

# Install dependencies
pip install -r requirements.txt

# Or use the setup script
./setup.sh
```

### 2. Set Up API Key

Create a `.env` file:

```bash
# Copy the example
cp .env.example .env

# Edit and add your OpenAI API key
nano .env  # or use your preferred editor
```

Your `.env` should look like:
```
OPENAI_API_KEY=sk-proj-abc123...
```

Get your API key at: https://platform.openai.com/api-keys

### 3. Run Your First Qualification

```bash
python main.py
```

This runs with 3 example leads. You'll see:
- Planning phase (with company deduplication)
- Research execution (mock data by default)
- Lead qualification scores
- Personalized LinkedIn messages
- Results saved to `output/`

### 4. View Results

**Option A: JSON (Full Details)**
```bash
cat output/qualified_leads.json | jq
```

**Option B: CSV (Spreadsheet)**
```bash
open output/qualified_leads.csv  # macOS
# or
excel output/qualified_leads.csv  # Windows
```

**Option C: Python Pretty Print**
```python
import json
with open('output/qualified_leads.json') as f:
    data = json.load(f)
    for lead in data:
        print(f"\n{lead['lead']['name']} - Score: {lead['qualification']['score']}")
        if lead['personalized_copy']:
            print(f"LinkedIn Message: {lead['personalized_copy']['linkedin_message']}")
```

---

## Adding Your Own Leads

### Method 1: Edit main.py Directly

```python
leads = [
    Lead(
        id="lead_1",
        name="Sarah Chen",
        linkedin_url="https://linkedin.com/in/sarahchen",
        company_name="Stripe",
        title="Engineering Manager"
    ),
    Lead(
        id="lead_2",
        name="Michael Torres",
        linkedin_url="https://linkedin.com/in/michaeltorres",
        company_name="Stripe",  # Same company - will be deduplicated!
        title="VP of Engineering"
    ),
    # Add more...
]
```

### Method 2: Load from CSV

**Create `my_leads.csv`:**
```csv
id,name,linkedin_url,company_name,title
lead_1,Sarah Chen,https://linkedin.com/in/sarahchen,Stripe,Engineering Manager
lead_2,Michael Torres,https://linkedin.com/in/michaeltorres,Stripe,VP of Engineering
```

**Load in main.py:**
```python
leads = load_leads_from_csv('my_leads.csv')
```

### Method 3: Export from Sales Navigator

1. Export your Sales Navigator search to CSV
2. Rename columns to match: `name`, `linkedin_url`, `company_name`, `title`
3. Add an `id` column (can be sequential: lead_1, lead_2, etc.)
4. Load using `load_leads_from_csv()`

---

## Customizing Your Campaign

Edit the `CAMPAIGN_CONTEXT` in `main.py`:

```python
CAMPAIGN_CONTEXT = """
We're selling [YOUR PRODUCT/SERVICE].

Target Profile:
- [Job Titles] at [Company Types]
- Company size: [Size Range]
- Industry: [Industries]
- Pain points: [Problems They Face]

Value Proposition:
- [Benefit 1 with metric]
- [Benefit 2 with metric]
- [Benefit 3 with metric]

Pricing: [Pricing Model]

Examples of Good Fit:
- [Example 1]
- [Example 2]
"""
```

**Example for DevTools:**
```python
CAMPAIGN_CONTEXT = """
We're selling an API monitoring and debugging tool for backend teams.

Target Profile:
- Backend Engineering Leads, Staff Engineers, or DevOps Managers
- Series A-C startups with 50-500 employees
- Companies with microservices architecture
- Pain points: API downtime, slow debugging, incident response delays

Value Proposition:
- Reduce MTTR (Mean Time To Repair) by 60%
- Catch API issues before customers do
- Full request/response inspection with context

Pricing: $299/month for teams up to 20 engineers

Examples of Good Fit:
- Recently raised funding and scaling team
- Posted about debugging challenges or outages
- Using modern tech stack (Node.js, Python, Go)
"""
```

---

## Understanding the Output

### Qualification Scores

| Score | Priority | Meaning | Action |
|-------|----------|---------|--------|
| 80-100 | High | Perfect fit - strong signals | Reach out immediately |
| 60-79 | High | Good fit - matches ICP | Reach out within 1-2 days |
| 40-59 | Medium | Moderate fit - needs review | Manual review, reach out if validated |
| 0-39 | Low | Poor fit or missing data | Skip or deprioritize |

**Copy Generation Threshold:**
- By default, only leads scoring ≥ 50 get personalized copy
- Adjust in main.py: `qualification_threshold=50`

### Output File Structure

**qualified_leads.json:**
```json
{
  "lead": { /* Basic info */ },
  "qualification": {
    "score": 85,
    "priority": "high",
    "fit_reasons": [/* Why they're a good fit */],
    "red_flags": [/* Concerns */],
    "key_insights": [/* Personalization hooks */]
  },
  "personalized_copy": {
    "linkedin_message": "...",
    "email_body": "...",
    "subject_line": "...",
    "talking_points": [...]
  },
  "research_summary": {
    "profile_highlights": [...],
    "company_highlights": [...],
    "recent_activity": [...]
  }
}
```

**qualified_leads.csv:**
Simplified view with just the essentials:
- Name, title, company
- Score, priority
- LinkedIn message (ready to copy/paste)
- Email subject line

---

## Configuration Options

### In main.py

```python
agent = SalesQualificationAgent(
    campaign_context=CAMPAIGN_CONTEXT,

    # Model for planning & qualification (cheap & fast)
    model="gpt-4o-mini",

    # Model for copy generation (better quality)
    copy_model="gpt-4o",

    # Only generate copy for leads scoring >= this
    qualification_threshold=50,

    # Where to save research data
    context_dir=".leads/context",
)
```

### Available Models

| Model | Speed | Cost | Use For |
|-------|-------|------|---------|
| gpt-4o-mini | Fast | $0.15/$0.60 per 1M tokens | Planning, qualification |
| gpt-4o | Medium | $2.50/$10 per 1M tokens | Copy generation |
| gpt-4-turbo | Medium | $10/$30 per 1M tokens | High-quality copy |
| gpt-3.5-turbo | Very Fast | $0.50/$1.50 per 1M tokens | Budget option |

**Cost Estimate (per lead):**
- Planning: ~500 tokens (~$0.0005 with gpt-4o-mini)
- Qualification: ~1000 tokens (~$0.001 with gpt-4o-mini)
- Copy generation: ~1500 tokens (~$0.015 with gpt-4o)
- **Total: ~$0.02 per lead** (with default settings)

---

## Troubleshooting

### "OPENAI_API_KEY environment variable not set"

**Solution:**
1. Create `.env` file in project root
2. Add: `OPENAI_API_KEY=sk-proj-...`
3. Get key from: https://platform.openai.com/api-keys

### "ModuleNotFoundError: No module named 'langchain'"

**Solution:**
```bash
pip install -r requirements.txt
```

### "Rate limit exceeded"

You hit OpenAI's rate limits.

**Solutions:**
- Wait a few minutes and retry
- Reduce batch size (process 5-10 leads at a time)
- Upgrade your OpenAI plan

### Results show "No profile data"

This is normal without RapidAPI key. The system uses mock data for testing.

**To get real LinkedIn data:**
1. Get RapidAPI key: https://rapidapi.com
2. Subscribe to a LinkedIn scraping API
3. Add to `.env`: `RAPIDAPI_KEY=your-key`

### Low qualification scores (all < 40)

**Possible causes:**
1. Campaign context too narrow/specific
2. Mock data doesn't match your ICP
3. LLM being conservative

**Solutions:**
- Review and broaden your `CAMPAIGN_CONTEXT`
- Test with real LinkedIn data (add RAPIDAPI_KEY)
- Adjust scoring in prompts (see Advanced Usage docs)

---

## Next Steps

- [Architecture Guide](./ARCHITECTURE.md) - Understand how it works
- [Customization Guide](./CUSTOMIZATION.md) - Add features, modify behavior
- [API Reference](./API_REFERENCE.md) - Code documentation
- [Best Practices](./BEST_PRACTICES.md) - Tips for effective lead qualification

---

## Quick Tips

✅ **Start small**: Test with 3-5 leads first
✅ **Review scores**: Don't trust AI blindly, review before sending
✅ **Iterate campaign context**: Refine based on results
✅ **Monitor costs**: Check OpenAI usage dashboard
✅ **Batch process**: Process 10-20 leads at a time
✅ **Save good examples**: Build a library of successful copy

---

## Need Help?

- Check the [FAQ](./FAQ.md)
- Review [Common Issues](./TROUBLESHOOTING.md)
- Open an issue on GitHub
