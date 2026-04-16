import os
import json
import re
import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


def clean_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def classify_gtm_motion(company, raw_data):
    jobs = raw_data.get("jobs", [])
    web = raw_data.get("web", [])
    news = raw_data.get("news", "")

    job_titles = [j["title"] for j in jobs]
    web_snippets = [f"{w['title']}: {w['snippet']}" for w in web[:8]]

    prompt = f"""You are a B2B market analyst specialising in go-to-market strategy.

Analyse the GTM motion of {company} based on the data below.

Job postings ({len(job_titles)} roles):
{chr(10).join(job_titles) if job_titles else "No job data available."}

Web content snippets:
{chr(10).join(web_snippets)}

Recent news:
{news}

Classify their GTM motion. Return ONLY a JSON object with this exact schema:
{{
  "classification": "PLG" | "SLG" | "Channel-led" | "PLG-SLG hybrid" | "Insufficient data",
  "confidence": "high" | "medium" | "low",
  "plg_signals": ["list of specific PLG signals found"],
  "slg_signals": ["list of specific SLG signals found"],
  "rationale": "2-3 sentence explanation citing specific evidence from the data"
}}

If data is insufficient to classify with confidence, use "Insufficient data" as classification.
Return only the JSON, no other text."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(clean_json(response.content[0].text))
    except Exception as e:
        print(f"GTM parse error: {e}\nRaw: {response.content[0].text}")
        return {
            "classification": "Insufficient data",
            "confidence": "low",
            "plg_signals": [],
            "slg_signals": [],
            "rationale": "Could not parse response."
        }


def extract_pricing_intel(company, raw_data):
    web = raw_data.get("web", [])
    pricing_snippets = [
        f"{w['title']}: {w['snippet']}"
        for w in web
        if any(kw in w.get("url", "").lower() or kw in w.get("title", "").lower()
               for kw in ["pric", "plan", "cost", "tier"])
    ]

    if not pricing_snippets:
        pricing_snippets = [f"{w['title']}: {w['snippet']}" for w in web[:6]]

    prompt = f"""You are a B2B pricing strategist.

Extract pricing intelligence for {company} from the data below.

Pricing-related web content:
{chr(10).join(pricing_snippets)}

Return ONLY a JSON object with this exact schema:
{{
  "value_metric": "per-seat" | "usage-based" | "flat" | "freemium" | "contact-only" | "hybrid",
  "icp_signal": "individual" | "startup" | "SMB" | "mid-market" | "enterprise" | "mixed",
  "has_free_tier": true | false,
  "tier_names": ["list of visible tier names"],
  "entry_price": "lowest visible price point or null",
  "competitive_strategy": "price-compete" | "feature-compete" | "brand-compete" | "unclear",
  "rationale": "2-3 sentence explanation"
}}

Return only the JSON, no other text."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(clean_json(response.content[0].text))
    except Exception as e:
        print(f"Pricing parse error: {e}\nRaw: {response.content[0].text}")
        return {
            "value_metric": "unclear",
            "icp_signal": "unclear",
            "has_free_tier": False,
            "tier_names": [],
            "entry_price": None,
            "competitive_strategy": "unclear",
            "rationale": "Could not parse response."
        }


def score_feature_gaps(company, raw_data, jobs_to_be_done):
    web = raw_data.get("web", [])
    reviews = raw_data.get("reviews", {})
    news = raw_data.get("news", "")

    web_snippets = [f"{w['title']}: {w['snippet']}" for w in web[:8]]
    pros = reviews.get("pros", [])
    cons = reviews.get("cons", [])

    jobs_formatted = "\n".join([f"{i+1}. {job}" for i, job in enumerate(jobs_to_be_done)])

    prompt = f"""You are a product analyst conducting a Jobs-to-be-Done feature gap analysis.

Score {company} on each of the following customer jobs based on the data provided.

Jobs to score:
{jobs_formatted}

Data about {company}:

Web content:
{chr(10).join(web_snippets)}

Customer review pros:
{chr(10).join(pros) if pros else "No review data available."}

Customer review cons:
{chr(10).join(cons) if cons else "No review data available."}

Recent news:
{news}

Scoring rubric:
0 = Cannot do this job at all or no evidence it is possible
1 = Can do this job but with significant friction or workarounds
2 = Does this job well with minimal friction

Return ONLY a JSON array with this exact schema:
[
  {{
    "job": "exact job description as given",
    "score": 0 | 1 | 2,
    "rationale": "one sentence citing specific evidence"
  }}
]

Score every job. If there is no evidence, default to 1.
Return only the JSON array, no other text."""

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(clean_json(response.content[0].text))
    except Exception as e:
        print(f"Feature gap parse error: {e}\nRaw: {response.content[0].text}")
        return [{"job": job, "score": 1, "rationale": "Could not parse response."} for job in jobs_to_be_done]


def generate_executive_summary(target_company, competitors_analysis):
    summary_data = json.dumps(competitors_analysis, indent=2)

    prompt = f"""You are a senior strategy consultant.

Write an executive summary of the competitive landscape for {target_company} based on the analysis below.

{summary_data}

The summary must:
1. Identify the dominant GTM motion in the market
2. Call out the most significant pricing pattern
3. Name the clearest feature gap or market opportunity
4. End with one strategic recommendation for {target_company}

Write in 4 short paragraphs. Be direct and specific. No generic statements."""

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text


if __name__ == "__main__":
    test_data = {
        "web": [
            {"title": "Notion Pricing", "snippet": "Free plan available. Plus plan at $10/month per seat. Business plan at $18/month per seat.", "url": "notion.so/pricing"},
            {"title": "Notion Review", "snippet": "Notion is a product-led tool loved by individuals and small teams for docs and wikis.", "url": "g2.com/notion"},
            {"title": "Notion Case Study PLG", "snippet": "Notion grew to 30 million users through bottom-up product-led growth with no outbound sales team.", "url": "linkedin.com/notion"}
        ],
        "jobs": [],
        "reviews": {
            "pros": ["Very flexible", "Great for docs"],
            "cons": ["Slow with large databases", "Overwhelming for simple tasks"]
        },
        "news": "Notion launched AI features across all plans in early 2024."
    }

    print("Testing GTM classification...")
    gtm = classify_gtm_motion("Notion", test_data)
    print(json.dumps(gtm, indent=2))

    print("\nTesting pricing intel...")
    pricing = extract_pricing_intel("Notion", test_data)
    print(json.dumps(pricing, indent=2))

    print("\nTesting feature gap scoring...")
    jobs = [
        "Get started without talking to sales",
        "Track projects across teams in one view",
        "Integrate with existing tools without engineering help"
    ]
    gaps = score_feature_gaps("Notion", test_data, jobs)
    print(json.dumps(gaps, indent=2))