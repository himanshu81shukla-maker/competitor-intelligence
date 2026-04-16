import os
import requests
import anthropic
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

SERPER_KEY = os.getenv("SERPER_API_KEY")
ADZUNA_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_KEY = os.getenv("ADZUNA_APP_KEY")


def fetch_web_search(company):
    queries = [
        f"{company} pricing plans 2024",
        f"{company} product features overview",
        f"{company} customer case study"
    ]
    results = []
    for q in queries:
        try:
            r = requests.post(
                "https://google.serper.dev/search",
                headers={"X-API-KEY": SERPER_KEY, "Content-Type": "application/json"},
                json={"q": q, "num": 5},
                timeout=10
            )
            organic = r.json().get("organic", [])
            results.extend([{
                "query": q,
                "title": item.get("title"),
                "snippet": item.get("snippet"),
                "url": item.get("link")
            } for item in organic])
        except Exception as e:
            print(f"Serper error for {company}: {e}")
    return results


def fetch_job_postings(company):
    try:
        r = requests.get(
            "https://api.adzuna.com/v1/api/jobs/us/search/1",
            params={
                "app_id": ADZUNA_ID,
                "app_key": ADZUNA_KEY,
                "what_and": company,
                "results_per_page": 20,
                "content-type": "application/json"
            },
            timeout=10
        )
        jobs = r.json().get("results", [])
        return [{
            "title": j.get("title"),
            "description": j.get("description", "")[:400],
            "location": j.get("location", {}).get("display_name", ""),
            "created": j.get("created")
        } for j in jobs]
    except Exception as e:
        print(f"Adzuna error for {company}: {e}")
        return []


def fetch_reviews(company):
    slug = company.lower().replace(" ", "-").replace(".", "")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    pros, cons, rating = [], [], "N/A"
    try:
        url = f"https://www.g2.com/products/{slug}/reviews"
        r = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        pros = [p.get_text(strip=True) for p in soup.select(".pros p")[:5]]
        cons = [c.get_text(strip=True) for c in soup.select(".cons p")[:5]]
        rating_tag = soup.select_one("[itemprop='ratingValue']")
        if rating_tag:
            rating = rating_tag.get("content", "N/A")
    except Exception as e:
        print(f"G2 error for {company}: {e}")
    return {"source": "g2", "rating": rating, "pros": pros, "cons": cons}


def fetch_news(company):
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": f"""Summarise what is publicly known about {company} across these areas:
1. Recent product launches or major feature releases
2. Funding rounds or valuation milestones
3. Key partnerships or acquisitions
4. Strategic direction or market expansion

Write 4 to 6 bullet points. Be factual and concise. Do not mention anything about knowledge cutoffs or training data. If you are unsure about a specific date, omit the date and state the fact only."""
            }]
        )
        return response.content[0].text
    except Exception as e:
        print(f"News error for {company}: {e}")
        return "News data unavailable."


def collect_all(company):
    print(f"Collecting data for {company}...")
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(fetch_web_search, company): "web",
            executor.submit(fetch_job_postings, company): "jobs",
            executor.submit(fetch_reviews, company): "reviews",
            executor.submit(fetch_news, company): "news"
        }
        results = {}
        for future in as_completed(futures):
            key = futures[future]
            results[key] = future.result()
    print(f"Done collecting for {company}.")
    return results