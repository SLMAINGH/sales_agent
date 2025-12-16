"""
Test webhook endpoint with a local webhook receiver.

Run this to test the async webhook flow:
1. Starts a simple webhook receiver on port 8001
2. Sends a test request to the API
3. Receives and displays the webhook callback
"""
import asyncio
import json
import requests
import time
from fastapi import FastAPI, Request
import uvicorn
from threading import Thread

# Simple webhook receiver
webhook_app = FastAPI()
received_data = []


@webhook_app.post("/webhook")
async def receive_webhook(request: Request):
    """Receive webhook callback from the API."""
    data = await request.json()
    received_data.append(data)
    print("\n" + "="*80)
    print("📨 WEBHOOK RECEIVED!")
    print("="*80)
    print(json.dumps(data, indent=2))
    print("="*80 + "\n")
    return {"status": "received"}


def run_webhook_server():
    """Run webhook receiver in background."""
    uvicorn.run(webhook_app, host="127.0.0.1", port=8001, log_level="error")


def test_webhook_endpoint():
    """Test the webhook endpoint."""
    print("="*80)
    print("Testing Webhook Endpoint")
    print("="*80 + "\n")

    # Start webhook receiver in background
    print("1. Starting webhook receiver on http://127.0.0.1:8001...")
    webhook_thread = Thread(target=run_webhook_server, daemon=True)
    webhook_thread.start()
    time.sleep(2)  # Wait for server to start

    # Send request to API with webhook URL
    print("2. Sending lead to API with webhook URL...\n")

    api_url = "http://127.0.0.1:8000/qualify/webhook"
    payload = {
        "name": "John Smith",
        "linkedin_url": "https://linkedin.com/in/johnsmith",
        "company_name": "TechCorp",
        "title": "VP of Engineering",
        "webhook_url": "http://127.0.0.1:8001/webhook"
    }

    response = requests.post(api_url, json=payload)

    if response.status_code == 200:
        result = response.json()
        print("✅ API Response (Immediate):")
        print(json.dumps(result, indent=2))
        print("\n3. Processing lead in background...")
        print("4. Waiting for webhook callback...\n")

        # Wait for webhook (up to 60 seconds)
        timeout = 60
        start_time = time.time()
        while len(received_data) == 0 and (time.time() - start_time) < timeout:
            time.sleep(1)

        if received_data:
            print("\n✅ TEST PASSED!")
            print(f"\nQualification Score: {received_data[0]['data']['qualification']['score']}/100")
            print(f"Priority: {received_data[0]['data']['qualification']['priority']}")
        else:
            print("\n⚠️  Webhook not received within timeout")

    else:
        print(f"❌ API request failed: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Sales Qualification API - Webhook Test")
    print("="*80)
    print("\nMake sure the API is running on port 8000:")
    print("  uvicorn api:app --reload --port 8000")
    print("\nPress Ctrl+C to stop\n")

    input("Press Enter to start test...")

    test_webhook_endpoint()

    print("\n" + "="*80)
    print("Test complete. Webhook receiver still running...")
    print("Press Ctrl+C to exit")
    print("="*80 + "\n")

    # Keep running to receive more webhooks if needed
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
