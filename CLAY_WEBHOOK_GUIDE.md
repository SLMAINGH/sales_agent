# Clay Webhook Integration Guide

Use this guide if you're concerned about API timeout issues. The webhook pattern returns results asynchronously.

## How It Works

1. **Clay sends request** → API returns immediately (no waiting)
2. **API processes in background** → Takes 10-30 seconds
3. **API sends results to webhook** → Clay receives the data

## Clay Setup with Webhook

### Step 1: Get Your Clay Webhook URL

1. In your Clay table, click **"+ Add Enrichment"**
2. Search for **"Webhook"** or **"HTTP API"**
3. Clay will provide you a unique webhook URL like:
   ```
   https://webhooks.clay.com/webhook/xxxxx-xxxxx-xxxxx
   ```
4. **Copy this URL** - you'll pass it in the API request

### Step 2: Configure HTTP API Request

**Method:** `POST`

**URL:** `https://your-railway-url.up.railway.app/qualify/webhook`

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
  "title": "{{title}}",
  "webhook_url": "YOUR_CLAY_WEBHOOK_URL_HERE"
}
```

### Step 3: Map Webhook Response

When the webhook fires, Clay will receive:

```json
{
  "status": "success",
  "lead_id": "lead_john_smith",
  "data": {
    "lead": {...},
    "qualification": {
      "score": 85,
      "priority": "high",
      "fit_reasons": [...],
      "red_flags": [...],
      "key_insights": [...]
    },
    "personalized_copy": {
      "subject_line": "...",
      "email_body": "...",
      "linkedin_message": "...",
      "talking_points": [...]
    },
    "research_summary": {...}
  }
}
```

**Map these paths in Clay:**
- `/data/qualification/score` → Qualification Score
- `/data/qualification/priority` → Priority
- `/data/qualification/fit_reasons` → Fit Reasons
- `/data/personalized_copy/subject_line` → Email Subject
- `/data/personalized_copy/email_body` → Email Body
- `/data/personalized_copy/linkedin_message` → LinkedIn Message

## Comparison: Sync vs Webhook

### Synchronous (`/qualify`)
✅ Simpler setup
✅ Immediate results
❌ May timeout on slow processing
❌ Clay has to wait for each lead

**Best for:** Testing, small batches, fast processing

### Webhook (`/qualify/webhook`)
✅ No timeout issues
✅ Clay can process multiple leads in parallel
✅ More reliable for production
❌ Slightly more complex setup

**Best for:** Production, large batches, reliability

## Testing Locally

### Option 1: Use webhook.site

1. Go to https://webhook.site
2. Copy your unique URL
3. Test with cURL:

```bash
curl -X POST http://localhost:8000/qualify/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "company_name": "TechCorp",
    "title": "VP of Engineering",
    "webhook_url": "https://webhook.site/your-unique-id"
  }'
```

4. Check webhook.site to see the results arrive

### Option 2: Use Test Script

```bash
# Terminal 1: Start the API
uvicorn api:app --reload --port 8000

# Terminal 2: Run webhook test
python test_webhook.py
```

## Expected Timeline

| Step | Time |
|------|------|
| Clay sends request | Instant |
| API responds "accepted" | < 1 second |
| API processes lead | 10-30 seconds |
| Webhook delivers results | < 1 second |
| **Total** | **~10-30 seconds** |

The key difference: Clay doesn't wait! It continues processing other rows while your lead qualifies in the background.

## Error Handling

If processing fails, webhook receives:

```json
{
  "status": "error",
  "lead_id": "lead_john_smith",
  "error": "Error message here"
}
```

Map `/status` to check if the result succeeded or failed.

## Clay Workflow Example

```
1. Import leads to Clay table
2. Add HTTP API enrichment with webhook
3. API returns "accepted" immediately
4. Clay continues to next row
5. Results arrive via webhook (10-30s later)
6. Clay populates qualification data
```

**Pro tip:** Run 10-20 leads in parallel! The webhook pattern allows Clay to send multiple requests without waiting for each to complete.

## Webhook URL Security

Your Clay webhook URL is unique and secure. Only share it with trusted services.

**Best practices:**
- Don't commit webhook URLs to git
- Rotate URLs periodically in Clay
- Monitor for unexpected webhook calls

## Troubleshooting

### Webhook never arrives

**Check:**
1. API is running on Railway
2. OPENAI_API_KEY is set in Railway
3. Webhook URL is correct and accessible
4. Check Railway logs for errors: `railway logs`

### Webhook arrives but no data

**Check:**
1. Verify `/status` field = "success"
2. Check `/error` field if status = "error"
3. Ensure paths in Clay match response structure

### Multiple webhooks for same lead

This shouldn't happen, but if it does:
- Use `/lead_id` to deduplicate
- Check you're not accidentally triggering multiple requests

## Production Tips

1. **Start small:** Test with 5-10 leads first
2. **Monitor costs:** Each lead costs ~$0.01-0.02 in API calls
3. **Batch timing:** Process leads in groups of 20-50
4. **Rate limits:** Railway has no specific limits, but be reasonable
5. **Caching:** Consider caching results for leads you've already processed

## Need Help?

- Check Railway logs: `railway logs`
- Test webhook delivery: https://webhook.site
- Verify API health: `https://your-url.railway.app/health`

## Next Steps

1. ✅ Deploy API to Railway
2. ✅ Add OPENAI_API_KEY environment variable
3. ✅ Get Clay webhook URL
4. ✅ Configure HTTP API enrichment with webhook
5. ✅ Test on 1 lead
6. ✅ Run on full table

---

**Both sync and webhook endpoints are available!** Choose the one that fits your use case.
