"""
Main entry point for the sales qualification agent.
"""
import asyncio
import json
import csv
from pathlib import Path
from agent.schemas import Lead
from agent.sales_agent import SalesQualificationAgent


# Campaign context
CAMPAIGN_CONTEXT = """
We are selling Niteco's "Sitecore Modernization & XM Cloud Migration" services.

Our Value Proposition:
We help enterprises escape legacy Sitecore monolithic versions (XP 9/10) and migrate to a modern, composable stack (XM Cloud + Next.js) faster and with less risk than generalist agencies. We use a proprietary "Audit & Roadmap" methodology to guarantee fixed costs and timelines.

Target Profile:
- Role: CIOs, CTOs, VPs of Digital, and CMOs.
- Company Size: Mid-to-Enterprise (Revenue $200M+, 500+ employees).
- Industries: Manufacturing, Retail/Distribution, Healthcare, Finance.
- Tech Stack: Currently running Sitecore XP (Versions 8.x, 9.x, or 10.x) on-premise or via Azure PaaS.

Key Pain Points (The "Why Now"):
1. "The Monolith Trap": High Azure infrastructure costs and slow deployment cycles on legacy Sitecore XP.
2. "XM Cloud Anxiety": They know they need to move to SaaS/Headless (XM Cloud) but fear the complexity of rewriting the front-end (Next.js).
3. "Performance Issues": Slow page loads affecting Core Web Vitals and SEO rankings.
4. "Talent Gap": Struggle to find developers skilled in both legacy .NET Sitecore and modern React/Next.js.

The Offer (The Hook):
A "Sitecore Modernization Audit." We will analyze their current codebase and infrastructure to provide a fixed-price/fixed-timeline roadmap to XM Cloud, de-risking the migration.

Niteco Differentiators:
- Deep .NET & Sitecore Gold Partner pedigree.
- Proven "Upgrade Accelerator" methodology (similar to our Optimizely framework).
- Global delivery model ensuring 24/7 progress and cost-efficiency.
"""


def load_leads_from_csv(csv_path: str) -> list[Lead]:
    """Load leads from a CSV file."""
    leads = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            leads.append(Lead(
                id=row.get('id', f"lead_{i}"),
                name=row['name'],
                linkedin_url=row['linkedin_url'],
                company_name=row['company_name'],
                title=row['title'],
                sales_navigator_data={}
            ))
    return leads


def save_results_to_json(qualified_leads, output_path: str):
    """Save results to JSON file."""
    results = []
    for ql in qualified_leads:
        result = {
            "lead": {
                "name": ql.lead.name,
                "title": ql.lead.title,
                "company": ql.lead.company_name,
                "linkedin_url": ql.lead.linkedin_url,
            },
            "qualification": {
                "score": ql.qualification.score,
                "priority": ql.qualification.priority,
                "fit_reasons": ql.qualification.fit_reasons,
                "red_flags": ql.qualification.red_flags,
                "key_insights": ql.qualification.key_insights,
            },
            "personalized_copy": {
                "subject_line": ql.personalized_copy.subject_line,
                "email_body": ql.personalized_copy.email_body,
                "linkedin_message": ql.personalized_copy.linkedin_message,
                "talking_points": ql.personalized_copy.talking_points,
            } if ql.personalized_copy else None,
            "research_summary": {
                "profile_highlights": ql.research_summary.profile_highlights,
                "company_highlights": ql.research_summary.company_highlights,
                "recent_activity": ql.research_summary.recent_activity,
            }
        }
        results.append(result)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to {output_path}")


def save_results_to_csv(qualified_leads, output_path: str):
    """Save results to CSV file."""
    with open(output_path, 'w', newline='') as f:
        fieldnames = [
            'name', 'title', 'company', 'linkedin_url',
            'score', 'priority',
            'linkedin_message', 'subject_line'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ql in qualified_leads:
            writer.writerow({
                'name': ql.lead.name,
                'title': ql.lead.title,
                'company': ql.lead.company_name,
                'linkedin_url': ql.lead.linkedin_url,
                'score': ql.qualification.score,
                'priority': ql.qualification.priority,
                'linkedin_message': ql.personalized_copy.linkedin_message if ql.personalized_copy else '',
                'subject_line': ql.personalized_copy.subject_line if ql.personalized_copy else '',
            })

    print(f"💾 Results saved to {output_path}")


async def main():
    """Main function."""
    # Example: Create sample leads manually
    leads = [
        Lead(
            id="lead_1",
            name="John Smith",
            linkedin_url="https://linkedin.com/in/johnsmith",
            company_name="TechCorp",
            title="VP of Engineering"
        ),
        Lead(
            id="lead_2",
            name="Jane Doe",
            linkedin_url="https://linkedin.com/in/janedoe",
            company_name="TechCorp",  # Same company - will be deduplicated!
            title="CTO"
        ),
        Lead(
            id="lead_3",
            name="Bob Johnson",
            linkedin_url="https://linkedin.com/in/bobjohnson",
            company_name="StartupXYZ",
            title="Director of Engineering"
        ),
    ]

    # Or load from CSV:
    # leads = load_leads_from_csv('leads.csv')

    # Initialize agent
    agent = SalesQualificationAgent(
        campaign_context=CAMPAIGN_CONTEXT,
        model="gpt-4o-mini",  # Planning & qualification
        copy_model="gpt-4o",  # Copy generation (better model)
        qualification_threshold=50,  # Only generate copy for score >= 50
    )

    # Process leads
    qualified_leads = await agent.process_leads(leads, verbose=True)

    # Save results
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    save_results_to_json(qualified_leads, "output/qualified_leads.json")
    save_results_to_csv(qualified_leads, "output/qualified_leads.csv")

    # Print sample output
    print("\n" + "="*80)
    print("SAMPLE OUTPUT - First Lead:")
    print("="*80)
    if qualified_leads:
        ql = qualified_leads[0]
        print(f"\n👤 {ql.lead.name} - {ql.lead.title} at {ql.lead.company_name}")
        print(f"📊 Score: {ql.qualification.score}/100 ({ql.qualification.priority} priority)")
        print(f"\n✅ Fit Reasons:")
        for reason in ql.qualification.fit_reasons:
            print(f"   • {reason}")
        if ql.qualification.red_flags:
            print(f"\n⚠️  Red Flags:")
            for flag in ql.qualification.red_flags:
                print(f"   • {flag}")

        if ql.personalized_copy:
            print(f"\n📧 Email Subject: {ql.personalized_copy.subject_line}")
            print(f"\n💬 LinkedIn Message:")
            print(f"   {ql.personalized_copy.linkedin_message}")


if __name__ == "__main__":
    asyncio.run(main())
