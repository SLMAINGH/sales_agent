"""
Quick test script for the API endpoints.
Run this before deploying to Railway to verify everything works.
"""
import asyncio
import json
from api import app, LeadInput
from fastapi.testclient import TestClient

client = TestClient(app)


def test_health():
    """Test health endpoint."""
    print("Testing /health endpoint...")
    response = client.get("/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    assert response.status_code == 200


def test_qualify_single():
    """Test single lead qualification."""
    print("Testing /qualify endpoint...")

    lead_data = {
        "name": "John Smith",
        "linkedin_url": "https://linkedin.com/in/johnsmith",
        "company_name": "TechCorp",
        "title": "VP of Engineering"
    }

    response = client.post("/qualify", json=lead_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n👤 {result['lead']['name']} - {result['lead']['title']}")
        print(f"📊 Score: {result['qualification']['score']}/100")
        print(f"🎯 Priority: {result['qualification']['priority']}")
        print(f"\n✅ Fit Reasons:")
        for reason in result['qualification']['fit_reasons']:
            print(f"   • {reason}")

        if result['personalized_copy']:
            print(f"\n📧 Subject: {result['personalized_copy']['subject_line']}")
            print(f"\n💬 LinkedIn Message:")
            print(f"   {result['personalized_copy']['linkedin_message'][:200]}...")
    else:
        print(f"Error: {response.text}")

    print("\n")
    assert response.status_code == 200


def test_qualify_batch():
    """Test batch lead qualification."""
    print("Testing /qualify/batch endpoint...")

    batch_data = {
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
                "company_name": "TechCorp",  # Same company - will deduplicate!
                "title": "CTO"
            }
        ]
    }

    response = client.post("/qualify/batch", json=batch_data)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"\n📦 Batch Results:")
        print(f"   Total Processed: {result['total_processed']}")
        print(f"   Total Qualified: {result['total_qualified']}")
        print(f"\n   Leads:")
        for lead_result in result['results']:
            print(f"   • {lead_result['lead']['name']}: {lead_result['qualification']['score']}/100")
    else:
        print(f"Error: {response.text}")

    print("\n")
    assert response.status_code == 200


if __name__ == "__main__":
    print("="*80)
    print("Sales Qualification API - Test Suite")
    print("="*80 + "\n")

    try:
        test_health()
        test_qualify_single()
        test_qualify_batch()

        print("="*80)
        print("✅ All tests passed!")
        print("="*80)
        print("\nYou're ready to deploy to Railway! 🚀")
        print("\nNext steps:")
        print("1. Push to GitHub: git push")
        print("2. Deploy on Railway: railway.app")
        print("3. Set environment variables (OPENAI_API_KEY)")
        print("4. Test with your Railway URL")
        print("5. Integrate with Clay (see CLAY_INTEGRATION.md)")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        print("\nMake sure you have:")
        print("1. Created .env file with OPENAI_API_KEY")
        print("2. Installed dependencies: pip install -r requirements.txt")
