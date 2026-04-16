import json
import os
from data_collection import collect_all
from ai_analysis import (
    classify_gtm_motion,
    extract_pricing_intel,
    score_feature_gaps,
    generate_executive_summary
)

DEFAULT_JOBS = [
    "Get started and see value without talking to sales",
    "Track progress across multiple projects in one view",
    "Integrate with existing tools without engineering support",
    "Generate a status report in under 5 minutes",
    "Onboard a new team member without IT help",
    "Customise workflows without writing code",
    "Access the product on mobile without losing functionality",
    "Understand why a metric changed not just what it changed to",
    "Collaborate with external stakeholders without giving full access",
    "Scale usage without a disproportionate price increase"
]


def run_full_pipeline(target_company, competitor_names, jobs_to_be_done=None):
    if jobs_to_be_done is None:
        jobs_to_be_done = DEFAULT_JOBS

    all_companies = [target_company] + competitor_names
    competitors_analysis = []

    for company in all_companies:
        print(f"\nProcessing {company}...")

        raw_data = collect_all(company)

        gtm = classify_gtm_motion(company, raw_data)
        pricing = extract_pricing_intel(company, raw_data)
        gaps = score_feature_gaps(company, raw_data, jobs_to_be_done)

        company_result = {
            "name": company,
            "is_target": company == target_company,
            "gtm_motion": gtm,
            "pricing_intel": pricing,
            "job_scores": gaps,
            "news_summary": raw_data.get("news", ""),
            "top_reviews": raw_data.get("reviews", {})
        }

        competitors_analysis.append(company_result)
        print(f"Done with {company}.")

    print("\nGenerating executive summary...")
    summary = generate_executive_summary(target_company, competitors_analysis)

    final_output = {
        "target_company": target_company,
        "competitors": [c["name"] for c in competitors_analysis if not c["is_target"]],
        "jobs_to_be_done": jobs_to_be_done,
        "analysis": competitors_analysis,
        "executive_summary": summary
    }

    return final_output


if __name__ == "__main__":
    result = run_full_pipeline(
        target_company="Asana",
        competitor_names=["Notion", "Linear"]
    )
    os.makedirs("data", exist_ok=True)
    with open("data/test_run.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved to data/test_run.json")