# Quick Start - API Setup

Get the API running locally in 5 minutes, then deploy to Railway.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Set Up Environment

Edit `.env` and add your OpenAI API key:

```bash
OPENAI_API_KEY=sk-proj-xxxxx...
```

Get your key at: https://platform.openai.com/api-keys

## 3. Test Locally

```bash
# Run test suite
python test_api.py
```

Or start the server manually:

```bash
# Start the API server
uvicorn api:app --reload --port 8000
```

Visit: http://localhost:8000 (should see `{"status": "healthy"}`)

## 4. Test with cURL

```bash
# Health check
curl http://localhost:8000/health

# Qualify a lead
curl -X POST http://localhost:8000/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "company_name": "TechCorp",
    "title": "VP of Engineering"
  }'
```

## 5. Deploy to Railway

See [CLAY_INTEGRATION.md](./CLAY_INTEGRATION.md) for full deployment guide.

**Quick deploy:**

```bash
# Push to GitHub
git add .
git commit -m "Add API"
git push

# Deploy on Railway
# 1. Go to railway.app
# 2. New Project → Deploy from GitHub
# 3. Select your repo
# 4. Add OPENAI_API_KEY environment variable
# 5. Generate domain
```

## 6. Integrate with Clay

Once deployed, use your Railway URL in Clay's HTTP API enrichment:

**URL:** `https://your-app.up.railway.app/qualify`

See [CLAY_INTEGRATION.md](./CLAY_INTEGRATION.md) for detailed Clay setup.

## API Endpoints

### `GET /` - Root
Health check

### `GET /health` - Health Status
Check if API is configured correctly

### `POST /qualify` - Qualify Single Lead
Qualify one lead and generate personalized copy

**Request:**
```json
{
  "name": "John Smith",
  "linkedin_url": "https://linkedin.com/in/johnsmith",
  "company_name": "TechCorp",
  "title": "VP of Engineering"
}
```

**Response:**
```json
{
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
```

### `POST /qualify/batch` - Qualify Multiple Leads
Process multiple leads at once (automatically deduplicates company research)

**Request:**
```json
{
  "leads": [
    {
      "name": "John Smith",
      "linkedin_url": "...",
      "company_name": "TechCorp",
      "title": "VP of Engineering"
    },
    {
      "name": "Jane Doe",
      "linkedin_url": "...",
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

## Interactive API Docs

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

These provide interactive API testing and full documentation.

## Troubleshooting

**Import errors?**
```bash
pip install -r requirements.txt
```

**OpenAI API errors?**
- Check your API key is valid
- Verify you have credits: https://platform.openai.com/usage

**Port already in use?**
```bash
uvicorn api:app --reload --port 8001
```

**Need help?**
See [CLAY_INTEGRATION.md](./CLAY_INTEGRATION.md) for detailed troubleshooting.
