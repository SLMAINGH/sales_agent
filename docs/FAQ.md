# Frequently Asked Questions

## General Questions

### What does this tool do?

It automates lead qualification and personalized copy generation:
1. **Research**: Scrapes LinkedIn profiles, company data, news
2. **Qualify**: AI scores each lead (0-100) based on your criteria
3. **Personalize**: Generates custom LinkedIn messages and emails
4. **Export**: Outputs to JSON/CSV for your CRM

### How is this different from [tool X]?

Most tools focus on either data enrichment OR copy generation. This does both:
- **vs Clearbit/ZoomInfo**: Adds AI qualification + personalized copy
- **vs Lavender/Copy.ai**: Adds automated research + scoring
- **vs Manual process**: 10x faster, scalable

### How long does it take?

- **Per lead**: 10-15 seconds (with API calls)
- **10 leads**: ~2 minutes
- **100 leads**: ~15 minutes (parallelization helps)

### How much does it cost?

**OpenAI API costs** (main expense):
- Planning: ~$0.0001 per batch
- Research resolution: ~$0.0001 per lead
- Qualification: ~$0.0002 per lead
- Copy generation: ~$0.004 per lead (gpt-4o)

**Total: ~$0.005-0.01 per lead** depending on models used

RapidAPI (LinkedIn scraping) costs extra if you use it.

---

## Setup & Installation

### Do I need Python experience?

Basic Python helps, but not required. You'll need to:
- Edit `main.py` to add your leads/campaign
- Run `python main.py` in terminal
- That's it!

### What Python version?

Python 3.8+ required. Check with: `python --version`

### Installation fails - what do I do?

```bash
# Try upgrading pip first
pip install --upgrade pip

# Then retry
pip install -r requirements.txt

# If still failing, install one by one to see which package fails
pip install langchain
pip install langchain-openai
# ... etc
```

### Can I use Claude/Gemini instead of OpenAI?

Yes! The code supports multiple providers.

**For Anthropic (Claude):**
```python
# In model/llm.py, modify _get_llm:
from langchain_anthropic import ChatAnthropic

def _get_llm(model=None):
    return ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
```

**For Google (Gemini):**
```python
from langchain_google_genai import ChatGoogleGenerativeAI

def _get_llm(model=None):
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",
        google_api_key=os.getenv("GOOGLE_API_KEY")
    )
```

---

## Using the Tool

### Can I process leads without LinkedIn data?

Yes! The system uses mock data if RapidAPI key isn't set. Good for testing.

For real production use, you'd want real LinkedIn data (via RapidAPI) or manually input key info.

### How do I know which leads to prioritize?

The system assigns priority automatically:
- **High**: Score 70+ → Reach out immediately
- **Medium**: Score 50-69 → Review and reach out
- **Low**: Score < 50 → Skip or deprioritize

You can also sort by score in the CSV output.

### Should I send every generated message as-is?

**No!** Always review before sending:
- Check for accuracy (names, companies)
- Ensure tone matches your brand
- Verify any specific claims
- Add personal touch if needed

Think of it as a first draft that saves you 80% of the work.

### Can I process the same leads multiple times?

Yes, but it will re-do all research (costs money). The tool doesn't cache across runs.

To reuse research:
1. Keep the `.leads/context/` directory
2. Load existing data manually
3. Or implement caching (see Customization guide)

### How do I handle rate limits?

**OpenAI rate limits:**
- Use gpt-4o-mini for most tasks (higher limits)
- Process smaller batches (10-20 leads)
- Add delays between batches

**RapidAPI limits:**
- Check your plan's rate limit
- Add `time.sleep()` in tools if needed
- Process leads in smaller batches

---

## Results & Output

### All my leads scored low - why?

Common reasons:
1. **Campaign context too strict**: Broaden your ICP
2. **Mock data doesn't match ICP**: Real data will help
3. **LLM being conservative**: Adjust prompts to be less strict
4. **Leads actually don't fit**: The system is working correctly!

Try one known-good lead manually to test.

### No copy was generated - why?

Copy only generates if `score >= qualification_threshold` (default: 50).

Lower the threshold in `main.py`:
```python
agent = SalesQualificationAgent(
    qualification_threshold=40,  # Lower from 50
    ...
)
```

### The copy is too generic - how do I improve it?

1. **Better campaign context**: More specific = more personalized
2. **Real LinkedIn data**: Mock data → generic copy
3. **Adjust copy prompt**: See `agent/prompts.py:54`
4. **Use better model**: Switch to gpt-4o or gpt-4-turbo

### Can I see what data was collected?

Yes! Check `.leads/context/` directory:
```bash
ls -la .leads/context/
cat .leads/context/lead_1_get_linkedin_profile_abc123.json | jq
```

Each JSON file contains one tool's output.

---

## Customization

### Can I add custom qualification criteria?

Yes! Two approaches:

**1. Update campaign context** (easiest):
```python
CAMPAIGN_CONTEXT = """
...
Required criteria:
- Must be using Kubernetes in production [YOUR NEW CRITERION]
- Team size > 10 engineers
"""
```

**2. Add code logic** (more control):
See [CUSTOMIZATION.md](./CUSTOMIZATION.md#custom-qualification-logic)

### Can I change the tone of the copy?

Yes! Edit `agent/prompts.py:54`:
```python
COPY_GENERATION_SYSTEM_PROMPT = """
...
Tone: [CHANGE THIS]
- Casual and friendly [vs formal and professional]
- Use humor when appropriate [vs strictly business]
- Emoji okay [vs no emoji]
```

### Can I add more research sources?

Yes! See [CUSTOMIZATION.md](./CUSTOMIZATION.md#adding-custom-tools)

Popular additions:
- Crunchbase (funding data)
- GitHub (for developers)
- Twitter/X (social activity)
- Company tech stack (BuiltWith, Wappalyzer)

### Can I integrate with my CRM?

Yes! See examples in [CUSTOMIZATION.md](./CUSTOMIZATION.md#integrations):
- HubSpot
- Salesforce
- Pipedrive
- Or export CSV and import manually

---

## Troubleshooting

### "Invalid API key" error

**OpenAI:**
1. Check `.env` file exists in project root
2. Verify key starts with `sk-proj-` or `sk-`
3. Test key at https://platform.openai.com/playground
4. Regenerate if needed

**RapidAPI:**
1. Key format varies by provider
2. Check you're subscribed to the LinkedIn API
3. Verify subscription hasn't expired

### "Tool execution failed" messages

Usually means:
- API timeout (increase timeout in tools)
- Rate limit hit (slow down)
- Invalid parameters (check tool logs)
- API key issue

These are non-fatal - other tools will still work.

### Results missing some data

Check which tools failed:
```bash
# Look for "Tool execution failed" in output
python main.py | grep -i "failed"
```

Then investigate that specific tool.

### "Memory error" with large batches

Process in smaller batches:
```python
batch_size = 10
for i in range(0, len(all_leads), batch_size):
    batch = all_leads[i:i+batch_size]
    results = await agent.process_leads(batch)
```

### LinkedIn scraping not working

If using RapidAPI:
1. Verify RAPIDAPI_KEY is set
2. Check API subscription is active
3. Review rate limits on RapidAPI dashboard
4. Try different LinkedIn scraping API

Without RapidAPI, it uses mock data (expected).

---

## Best Practices

### Should I process all my leads at once?

No! Start small:
1. Test with 3-5 leads
2. Review results, iterate campaign context
3. Process 10-20 leads
4. Review and refine
5. Scale up to 50-100+

### How often should I run this?

Depends on your flow:
- **Weekly**: Process new leads from Sales Navigator export
- **Daily**: If you have high lead volume
- **On-demand**: When you have a specific target list

### Should I run this on my laptop or server?

**Laptop is fine** for:
- < 100 leads at a time
- Occasional use
- Testing/development

**Server/cloud recommended** for:
- 100+ leads regularly
- Automated scheduled runs
- Multiple team members

### How do I track what worked?

Add tracking to your copy:
```python
# In copy generation
linkedin_message = f"{base_message}\n\n(Ref: AI-{lead.id})"
```

Then track response rates by reference code in your CRM.

### What metrics should I track?

- **Qualification accuracy**: % of high-scored leads that convert
- **Response rate**: % who reply to your messages
- **Meeting booking rate**: % who book a call
- **Cost per qualified lead**: Total API costs / # qualified

Iterate campaign context based on these metrics.

---

## Advanced Topics

### Can I run this on a schedule?

Yes! Use cron (Linux/Mac) or Task Scheduler (Windows):

```bash
# crontab -e
0 9 * * * cd /path/to/sales-qualifier && python main.py
```

Or use a workflow tool like:
- GitHub Actions
- Zapier + Python anywhere
- AWS Lambda

### Can I make this a web app?

Yes! See the main README for interface options:
- Streamlit (easiest web UI)
- Flask/FastAPI (custom web app)
- Keep it CLI with better terminal UI (Rich library)

### Can multiple people use this?

Yes, but:
- Share the OpenAI API key (track costs)
- Each person runs locally, or
- Deploy as web app (see above)
- Use different `context_dir` per person to avoid conflicts

### How do I contribute improvements?

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request
5. Describe what you improved and why

Popular contributions:
- New tools (data sources)
- Better prompts
- Export formats
- Bug fixes

---

## Still Need Help?

- Review the other docs in `/docs`
- Check the code comments
- Open an issue on GitHub
- Email support (if provided)
