# Sales Qualifier API

AI-powered lead qualification with personalized outreach copy generation.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

## Run Locally

```bash
uvicorn api:app --reload --port 8000
```

## API Endpoints

### POST /qualify
Synchronous - returns results immediately
```bash
curl -X POST http://localhost:8000/qualify?verbose=true \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "company_name": "TechCorp",
    "title": "VP of Engineering"
  }'
```

### POST /qualify/webhook
Asynchronous - returns immediately, sends results to webhook
```bash
curl -X POST http://localhost:8000/qualify/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "linkedin_url": "https://linkedin.com/in/johnsmith",
    "company_name": "TechCorp",
    "title": "VP of Engineering",
    "webhook_url": "https://your-webhook-url.com"
  }'
```

## Deploy to Railway

1. Push to GitHub
2. Connect repo on railway.app
3. Add `OPENAI_API_KEY` environment variable
4. Generate domain

## Clay Integration

Use HTTP API enrichment with `/qualify/webhook` endpoint. Pass your Clay webhook URL in the request body.
