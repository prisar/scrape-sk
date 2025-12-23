
import requests
import time

BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"
HITS_PER_PAGE = 100
MAX_PAGES = 10  # Adjust if needed

def fetch_interesting_stories():
    all_results = []
    ai_ml_keywords = ["ai", "ml", "llm", "agentic", "reinforcement learning", "neural", "transformer", "gpt", "gan", "deep learning", "machine learning", "computer vision", "natural language processing", "robotics"]
    for page in range(MAX_PAGES):
        params = {
            "tags": "story",
            "hitsPerPage": HITS_PER_PAGE,
            "page": page
        }
        resp = requests.get(BASE_URL, params=params)
        if resp.status_code != 200:
            print(f"Failed at page {page}")
            break
        data = resp.json()
        hits = data.get("hits", [])
        if not hits:
            break

        for hit in hits:
            title = hit.get("title", "")
            if any(keyword in title.lower() for keyword in ai_ml_keywords):
                all_results.append({
                    "title": title,
                    "url": hit.get("url"),
                    "points": hit.get("points"),
                    "author": hit.get("author"),
                    "created_at": hit.get("created_at"),
                    "objectID": hit.get("objectID")
                })

        print(f"Fetched page {page}, total stories: {len(all_results)}")
        time.sleep(0.3)  # to avoid hitting rate limits

    return all_results

if __name__ == "__main__":
    stories = fetch_interesting_stories()
    # sort by points
    stories.sort(key=lambda x: x['points'], reverse=True)
    for s in stories:
        print(f"[{s['created_at']}] {s['title']} ({s['url']}) - {s['points']} points by {s['author']}")
