import requests
import time
import csv
import os
from datetime import datetime

BASE_URL = "https://hn.algolia.com/api/v1/search_by_date"
QUERY = "github.io"
HITS_PER_PAGE = 100
MAX_PAGES = 10  # Adjust if needed

def fetch_github_io_stories():
    all_results = []
    for page in range(MAX_PAGES):
        params = {
            "query": QUERY,
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
            url = hit.get("url", "")
            if "github.io" in url:
                all_results.append({
                    "title": hit.get("title"),
                    "url": url,
                    "points": hit.get("points"),
                    "author": hit.get("author"),
                    "created_at": hit.get("created_at"),
                    "objectID": hit.get("objectID")
                })

        print(f"Fetched page {page}, total stories: {len(all_results)}")
        time.sleep(0.3)  # to avoid hitting rate limits

    return all_results

if __name__ == "__main__":
    stories = fetch_github_io_stories()

    output_dir = "data/hackernews"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"hackernews_{timestamp}.csv")

    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['created_at', 'title', 'url', 'points', 'author', 'objectID'])

        for s in stories:
            writer.writerow([
                s['created_at'],
                s['title'],
                s['url'],
                s['points'],
                s['author'],
                s['objectID']
            ])

    print(f"Wrote {len(stories)} stories to {output_file}")

