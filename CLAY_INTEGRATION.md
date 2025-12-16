# Clay Integration Guide 🎨

Complete guide for deploying the Sales Qualifier API on Railway and integrating with Clay.

## Table of Contents
1. [Deploy to Railway](#deploy-to-railway)
2. [Configure Environment Variables](#configure-environment-variables)
3. [Test Your API](#test-your-api)
4. [Integrate with Clay](#integrate-with-clay)
5. [Clay Workflow Examples](#clay-workflow-examples)
6. [Troubleshooting](#troubleshooting)

---

## Deploy to Railway

### Option 1: Deploy from GitHub (Recommended)

1. **Push your code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

2. **Deploy on Railway**
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect the configuration from `railway.json` and `Procfile`

3. **Generate a domain**
   - Go to your project settings
   - Click "Generate Domain" under the Networking section
   - You'll get a URL like: `https://your-app.up.railway.app`

### Option 2: Deploy with Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up

# Generate domain
railway domain
```

---

## Configure Environment Variables

In your Railway project dashboard, add these environment variables:

### Required:
- `OPENAI_API_KEY` - Your OpenAI API key (get from platform.openai.com)

### Optional:
- `RAPIDAPI_KEY` - For real LinkedIn scraping (get from rapidapi.com)
  - Without this, the API uses mock data for testing

**To add variables:**
1. Go to your Railway project
2. Click on your service
3. Go to "Variables" tab
4. Add each key-value pair
5. Redeploy (Railway does this automatically)

---

## Test Your API

### Using cURL

```bash
# Replace with your Railway URL
export API_URL="https://your-app.up.railway.app"

# Health check
curl $API_URL/health

# Test single lead qualification
curl -X POST $API_URL/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "company_name": "TechCorp",
    "title": "VP of Engineering"
  }'
```

### Using Python

```python
import requests

API_URL = "https://your-app.up.railway.app"

# Test qualification
response = requests.post(f"{API_URL}/qualify", json={
    "name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "company_name": "TechCorp",
    "title": "VP of Engineering"
})

print(response.json())
```

---

## Integrate with Clay

### Step 1: Set Up Clay Table

1. Create a new Clay table
2. Add columns for your lead data:
   - `name` (text)
   - `linkedin_url` (text)
   - `company_name` (text)
   - `title` (text)

### Step 2: Add HTTP API Enrichment

1. In Clay, click "+ Add Enrichment"
2. Search for "HTTP API"
3. Configure the enrichment:

**Method:** `POST`

**URL:** `https://your-app.up.railway.app/qualify`

**Headers:**
```json
{
  "Content-Type": "application/json"
}
```

**Body:**
```json
{
  "name": "{{name}}",
  "linkedin_url": "{{linkedin_url}}",
  "company_name": "{{company_name}}",
  "title": "{{title}}"
}
```

### Step 3: Map Output Fields

Clay will receive a JSON response. Map these fields to your table:

**Qualification Data:**
- `/qualification/score` → Qualification Score
- `/qualification/priority` → Priority
- `/qualification/fit_reasons` → Fit Reasons
- `/qualification/red_flags` → Red Flags
- `/qualification/key_insights` → Key Insights

**Personalized Copy:**
- `/personalized_copy/subject_line` → Email Subject
- `/personalized_copy/email_body` → Email Body
- `/personalized_copy/linkedin_message` → LinkedIn Message
- `/personalized_copy/talking_points` → Talking Points

**Research Summary:**
- `/research_summary/profile_highlights` → Profile Highlights
- `/research_summary/company_highlights` → Company Highlights
- `/research_summary/recent_activity` → Recent Activity

### Step 4: Add Filters

Set up Clay filters based on qualification:

1. **Filter by Score:** Only show leads with `score >= 70`
2. **Filter by Priority:** Only `high` priority leads
3. **Has Copy:** Only leads where `personalized_copy` is not null

---

## Clay Workflow Examples

### Workflow 1: Basic Lead Qualification

```
LinkedIn URLs (Import)
    ↓
Enrich with Sales Qualifier API
    ↓
Filter: Score >= 60
    ↓
Export to CSV
```

### Workflow 2: Personalized Outreach

```
LinkedIn URLs (Import)
    ↓
Enrich with Sales Qualifier API
    ↓
Filter: Priority = "high"
    ↓
Use personalized_copy.email_body
    ↓
Send via Clay's Email Integration
```

### Workflow 3: Company Deduplication

For multiple leads at the same company, use Clay's native deduplication:

```
LinkedIn URLs (Import)
    ↓
Group by company_name
    ↓
Enrich with Sales Qualifier API (batch)
    ↓
Ungroup and filter
```

**Note:** The API automatically deduplicates company research, so you'll save API costs when processing multiple leads from the same company.

---

## Advanced: Custom Campaign Context

You can customize the qualification criteria per Clay table:

### Option 1: Fixed Context (API Default)

The API uses the default campaign context in `api.py`. To change it:

1. Edit `api.py` → `DEFAULT_CAMPAIGN_CONTEXT`
2. Redeploy to Railway
3. All requests use this context

### Option 2: Dynamic Context (Per Request)

Send a custom `campaign_context` in the request body:

**Clay HTTP API Body:**
```json
{
  "name": "{{name}}",
  "linkedin_url": "{{linkedin_url}}",
  "company_name": "{{company_name}}",
  "title": "{{title}}",
  "campaign_context": "We're selling {{your_product}}. Target: {{your_target}}..."
}
```

This allows different Clay tables to use different qualification criteria!

---

## Batch Processing (Advanced)

For processing multiple leads at once (faster, cheaper):

**Endpoint:** `POST /qualify/batch`

**Body:**
```json
{
  "leads": [
    {
      "name": "John Smith",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "company_name": "TechCorp",
      "title": "VP of Engineering"
    },
    {
      "name": "Jane Doe",
      "linkedin_url": "https://linkedin.com/in/janedoe",
      "company_name": "TechCorp",
      "title": "CTO"
    }
  ]
}
```

**Response:**
```json
{
  "results": [...],
  "total_processed": 2,
  "total_qualified": 1
}
```

**Benefits:**
- Automatic company research deduplication
- Faster processing (parallel execution)
- Lower API costs

**Clay Integration:**
- Use Clay's webhook or batch export
- Send batches of 10-50 leads per request
- Process results and re-import to Clay

---

## Troubleshooting

### API Returns 500 Error

**Check:**
1. Environment variables are set correctly in Railway
2. OPENAI_API_KEY is valid and has credits
3. Railway logs for detailed error messages

**View logs:**
```bash
railway logs
```

### API is Slow

**Reasons:**
- Cold start (first request after inactivity)
- Large batch processing
- LinkedIn API rate limits

**Solutions:**
- Keep the API warm with periodic health checks
- Process in smaller batches (10-20 leads)
- Upgrade Railway plan for more resources

### LinkedIn Data is Mock/Fake

**Reason:** No RAPIDAPI_KEY configured

**Solution:**
1. Sign up at rapidapi.com
2. Subscribe to a LinkedIn scraping API
3. Add RAPIDAPI_KEY to Railway environment variables

### Clay Can't Reach API

**Check:**
1. Railway domain is generated and active
2. API is deployed and running (check Railway dashboard)
3. URL in Clay matches Railway domain exactly
4. Headers include `Content-Type: application/json`

### High API Costs

**Optimize:**
1. Use `gpt-4o-mini` for both planning and copy (edit `api.py`)
2. Increase `qualification_threshold` to 70 (less copy generation)
3. Process in batches to deduplicate company research
4. Cache results in Clay to avoid re-processing

---

## Example Response

Here's what you'll get back from the API:

```json
{
  "lead": {
    "name": "John Smith",
    "title": "VP of Engineering",
    "company_name": "TechCorp",
    "linkedin_url": "https://linkedin.com/in/johnsmith"
  },
  "qualification": {
    "score": 85,
    "priority": "high",
    "fit_reasons": [
      "Senior engineering leader at tech company",
      "Company size matches target profile (50-500 employees)",
      "Posted about code review challenges recently"
    ],
    "red_flags": [],
    "key_insights": [
      "Recently transitioned to VP role (3 months ago)",
      "Active on LinkedIn - posts weekly about eng culture",
      "Company raised Series B funding last quarter"
    ]
  },
  "personalized_copy": {
    "subject_line": "Thoughts on your recent code review post",
    "email_body": "Hi John,\n\nI noticed your recent post about code review bottlenecks...",
    "linkedin_message": "Hi John, loved your recent thoughts on code reviews...",
    "talking_points": [
      "Reference his recent post about code reviews",
      "Mention company's recent Series B funding",
      "Ask about scaling eng processes post-funding"
    ]
  },
  "research_summary": {
    "profile_highlights": [
      "VP of Engineering at TechCorp",
      "10+ years in engineering leadership",
      "Previously at Google and Stripe"
    ],
    "company_highlights": [
      "Series B startup, $20M raised",
      "Building developer tools",
      "Team of ~150 employees"
    ],
    "recent_activity": [
      "Posted about code review challenges (3 days ago)",
      "Shared article on engineering culture (1 week ago)"
    ]
  }
}
```

---

## Cost Estimates

**Per Lead (with GPT-4o-mini):**
- Planning: ~$0.001
- Research: ~$0.002
- Qualification: ~$0.001
- Copy (GPT-4o): ~$0.01
- **Total: ~$0.014 per qualified lead**

**100 leads/month:**
- Qualified leads: ~$1.40
- OpenAI API: ~$5-10
- Railway hosting: $5/month (Hobby plan)
- **Total: ~$11-16/month**

**1000 leads/month:**
- Qualified leads: ~$14
- OpenAI API: ~$50-100
- Railway hosting: $20/month (Pro plan)
- **Total: ~$84-134/month**

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Add environment variables
3. ✅ Test with cURL/Postman
4. ✅ Set up Clay HTTP API enrichment
5. ✅ Map output fields in Clay
6. ✅ Run on a small batch (5-10 leads)
7. ✅ Verify results
8. ✅ Scale to full lead list

---

## Support

- Railway Docs: https://docs.railway.app
- Clay API Docs: https://clay.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com

## Updates

To update your deployed API:

```bash
# Make changes locally
git add .
git commit -m "Update API"
git push

# Railway auto-deploys on push
```

Or use Railway CLI:
```bash
railway up
```
