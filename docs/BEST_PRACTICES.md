# Best Practices for Lead Qualification

Tips for getting the best results from the sales qualification agent.

## Campaign Setup

### ✅ Write a Strong Campaign Context

**Good Example:**
```python
CAMPAIGN_CONTEXT = """
We're selling a developer productivity tool that reduces PR review time by 50%.

Target Profile:
- Engineering Managers, VPs of Engineering at Series A-C startups
- Team size: 10-100 engineers
- Using GitHub/GitLab
- Pain: Long PR review cycles (>24 hours average), blocking deployments

Value Proposition:
- Reduce review time from 24h to <12h
- Automated code quality checks before human review
- Smart reviewer assignment based on expertise

Pricing: $49/developer/month

Ideal signals:
- Posted about slow code reviews or deployment bottlenecks
- Company raised funding in last 12 months (scaling pain)
- Job postings for senior engineers (team growing)
"""
```

**Why it works:**
- Specific numbers (50%, 24h, $49)
- Clear pain point articulated
- Concrete buying signals
- Realistic ICP (not too broad/narrow)

**Bad Example:**
```python
CAMPAIGN_CONTEXT = """
We help companies with software development.
Target: Any tech company.
We make development better and faster.
"""
```

**Why it fails:**
- Too vague ("help with software")
- No specific ICP
- No measurable value prop
- No qualification criteria

### ✅ Start Narrow, Then Broaden

**Phase 1:** Test with ideal fit
```python
# Super specific - confirm system works
Target: VPs of Engineering at Series B SaaS companies, 50-200 employees
```

**Phase 2:** Expand gradually
```python
# Add Directors
Target: VPs and Directors of Engineering...
```

**Phase 3:** Test adjacent segments
```python
# Test DevOps leaders
Target: VPs/Directors of Engineering and DevOps Managers...
```

Don't start with "anyone in tech" - you'll get poor qualification.

---

## Lead Selection

### ✅ Quality Over Quantity

**Better:**
- 20 well-researched leads from Sales Navigator
- Filtered by job title, company size, recent activity
- Matches your ICP closely

**Worse:**
- 1000 scraped emails
- No filtering or segmentation
- "Spray and pray" approach

The AI qualification helps, but garbage in = garbage out.

### ✅ Batch Leads by Segment

Process different segments separately:

```python
segments = {
    "enterprise": enterprise_leads,      # Different campaign context
    "smb": smb_leads,                    # Different value props
    "technical": technical_decision_makers,  # Different messaging
}

for segment_name, leads in segments.items():
    campaign_context = CAMPAIGN_CONTEXTS[segment_name]
    agent = SalesQualificationAgent(campaign_context=campaign_context)
    results = await agent.process_leads(leads)
```

**Why:** Better personalization than one-size-fits-all.

### ✅ Include Company Diversity

**Good batch:**
- 10 leads from 8-10 different companies
- Mix of company sizes, stages

**Bad batch:**
- 10 leads all from Google
- All same role/seniority

**Why:** Company deduplication optimizes for diversity. All leads from one company share research → less varied qualification.

---

## Running the Agent

### ✅ Test Small First

**Workflow:**
1. Run with 2-3 known-good leads
2. Review output carefully
3. Iterate campaign context
4. Expand to 10 leads
5. Review again
6. Scale to 50-100+

**Don't:** Process 500 leads on first run.

### ✅ Review API Costs

Before large batches:

```python
# Estimate costs
num_leads = 100
cost_per_lead = 0.01  # ~$0.01 with default settings
total_cost = num_leads * cost_per_lead
print(f"Estimated cost: ${total_cost}")

# Check your OpenAI balance
# https://platform.openai.com/usage
```

### ✅ Monitor Output Quality

After each run, check:
- Are scores reasonable? (mix of high/medium/low)
- Is copy personalized? (mentions specific activity)
- Any errors in tool execution?
- Do fit_reasons make sense?

**Red flags:**
- All leads score 90+ (too lenient)
- All leads score <30 (too strict or bad data)
- Generic copy (no personalization)
- Many tool failures

### ✅ Save Intermediate Results

```python
# Save research data even if qualification fails
agent = SalesQualificationAgent(
    context_dir=f".leads/context_{datetime.now().strftime('%Y%m%d')}"
)
```

**Why:** Can debug issues, reuse data, avoid re-running expensive API calls.

---

## Copy Review & Usage

### ✅ Always Review Before Sending

**Check for:**
- [ ] Factually accurate (names, companies correct)
- [ ] Tone matches your brand
- [ ] Not overpromising
- [ ] CTA is clear and appropriate
- [ ] No hallucinated details

**Example issues to catch:**
- "I saw you worked at Google" (they didn't)
- "Your recent Series B" (it was Series A)
- Wrong job title or company name

### ✅ Add Human Touch

The AI copy is a great **first draft** (~80% done). Add:

**Personal greeting:**
```
Before: Hi John,
After:  Hi John, hope you're having a great week.
```

**Specific mutual connection:**
```
Before: I noticed your role at TechCorp
After:  I noticed your role at TechCorp (btw, I worked with Sarah Chen there in 2020)
```

**Timely reference:**
```
Before: Loved your recent post
After:  Loved your recent post from Tuesday about code reviews
```

### ✅ A/B Test Your Approach

Test different variations:

**Variant A: Direct CTA**
```
Can we schedule 15 minutes this Thursday or Friday?
```

**Variant B: Soft CTA**
```
Would you be open to a brief chat if I shared how we helped similar teams?
```

Track response rates and iterate.

### ✅ Segment by Priority

**High priority (70-100):**
- Send immediately
- Personalize even further
- LinkedIn + email multi-touch

**Medium priority (50-69):**
- Review before sending
- May need more research
- LinkedIn first, email follow-up

**Low priority (<50):**
- Review and reconsider
- Possible they're not a fit
- Skip or manual review

---

## Optimization

### ✅ Iterate on Campaign Context

After each batch, refine based on results:

**Bad results (all low scores):**
```python
# Too narrow
"Must be VP at Series B, 100-150 employees, in SF, using React"
↓
# Broaden criteria
"VP or Director of Engineering at Series A-C, 50-500 employees"
```

**Too many false positives:**
```python
# Too broad
"Any engineering leader"
↓
# Add specificity
"Engineering leaders at B2B SaaS companies with >10 engineers"
```

### ✅ Track Conversion Metrics

Create a feedback loop:

```python
# Track in your CRM
{
    "lead_id": "lead_123",
    "qualification_score": 85,
    "copy_sent": "...",
    "response_received": True,
    "meeting_booked": True,
    "closed_won": False
}

# Analyze periodically
# - Do high scores actually convert better?
# - Which copy variants perform best?
# - Which data sources are most predictive?
```

Adjust campaign context and prompts based on what actually works.

### ✅ Build a Playbook

Document what works:

```markdown
## High-Converting Lead Profile
- Job title: VP or Director of Engineering
- Company: 50-200 employees, Series A-B
- Signal: Posted about relevant topic in last 30 days
- Company: Recently raised funding

## Best Performing Copy
- Subject line: Reference their recent post
- Opening: Specific pain point from their content
- CTA: "15-min call this week"

## Disqualifiers
- Consultants/agencies (not end users)
- Company < 10 employees (too early)
- No recent LinkedIn activity (won't see message)
```

Share with your team, iterate together.

---

## Scaling

### ✅ Automate Workflows

Once dialed in, automate:

```python
# schedule.py
import schedule
import time

def run_daily_qualification():
    leads = fetch_new_leads_from_sales_nav()
    agent = SalesQualificationAgent(CAMPAIGN_CONTEXT)
    results = await agent.process_leads(leads)
    send_to_crm(results)
    notify_team_slack(results)

schedule.every().day.at("09:00").do(run_daily_qualification)

while True:
    schedule.run_pending()
    time.sleep(60)
```

### ✅ Batch Processing for Large Lists

```python
def process_large_list(all_leads, batch_size=20):
    """Process leads in batches to manage costs and rate limits."""
    results = []

    for i in range(0, len(all_leads), batch_size):
        batch = all_leads[i:i+batch_size]
        print(f"Processing batch {i//batch_size + 1}/{len(all_leads)//batch_size + 1}")

        batch_results = await agent.process_leads(batch)
        results.extend(batch_results)

        # Save intermediate results
        save_results(batch_results, f"output/batch_{i}.json")

        # Rate limiting
        if i + batch_size < len(all_leads):
            time.sleep(10)  # Wait between batches

    return results
```

### ✅ Monitor Costs

```python
# Track costs per run
import time

start_time = time.time()
results = await agent.process_leads(leads)
elapsed = time.time() - start_time

estimated_cost = len(leads) * 0.01  # ~$0.01/lead
print(f"Processed {len(leads)} leads in {elapsed:.1f}s")
print(f"Estimated cost: ${estimated_cost:.2f}")
```

Set up alerts if costs exceed threshold.

---

## Common Mistakes to Avoid

### ❌ Don't Skip the Campaign Context

**Wrong:** Use default example context for your product
**Right:** Spend 15 minutes writing specific context

The campaign context drives everything - it's worth the time.

### ❌ Don't Blindly Trust AI Scores

**Wrong:** Auto-send to all leads scoring >80
**Right:** Review high-priority leads before sending

AI makes mistakes. Always have human oversight.

### ❌ Don't Use Exact Same Message for Everyone

**Wrong:** Copy/paste the generated LinkedIn message as-is
**Right:** Use as template, add 1-2 personal sentences

Generic = ignored. Even slight personalization helps.

### ❌ Don't Ignore Failed Tools

**Wrong:** "Some tools failed but I got results, ship it"
**Right:** Investigate why tools failed, fix before scaling

Failed tools = incomplete data = poor qualification.

### ❌ Don't Process Leads Without Research

**Wrong:** Scrape emails, run through agent, blast them all
**Right:** Pre-filter leads, use agent to enhance qualification

Agent is qualification+copy, not "make bad leads good".

### ❌ Don't Set Unrealistic Thresholds

**Wrong:** Only contact leads scoring 90+
**Right:** Test different thresholds (60, 70, 80) and measure

Being too selective = missing good opportunities.

---

## Success Checklist

Before running in production:

- [ ] Campaign context is specific and detailed
- [ ] Tested with 3-5 known-good leads
- [ ] Reviewed output quality carefully
- [ ] Adjusted prompts if needed
- [ ] Set appropriate qualification threshold
- [ ] Planned review process for generated copy
- [ ] Set up cost tracking/alerts
- [ ] Documented your workflow
- [ ] Tested with 10-20 lead batch
- [ ] Established feedback loop (track conversions)

---

## Resources

- [Getting Started Guide](./GETTING_STARTED.md)
- [Architecture Overview](./ARCHITECTURE.md)
- [Customization Guide](./CUSTOMIZATION.md)
- [FAQ](./FAQ.md)
