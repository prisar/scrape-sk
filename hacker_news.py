import requests
import time
import csv
import sys

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

    # Write CSV to stdout
    writer = csv.writer(sys.stdout)
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

