import requests
from bs4 import BeautifulSoup

url = 'https://export.arxiv.org/list/cs.AI/pastweek?show=1000'
useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"

print("Fetching URL...")
response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
print(f"Status code: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')

# Find first dt/dd pair
dt = soup.find('dt')
print(f"Found dt: {dt is not None}")

if dt:
    print("\n=== DT HTML structure ===")
    print(dt.prettify())
    print(f"DT text: {dt.get_text()}")

    dd = dt.find_next_sibling('dd')
    print(f"\nFound dd: {dd is not None}")
    if dd:
        print("\n=== DD HTML structure ===")
        print(dd.prettify())

        # Check siblings after dd
        print("\n\n=== Checking siblings after dd ===")
        next_sibling = dd.find_next_sibling()
        for i in range(3):
            if next_sibling:
                print(f"\nSibling #{i}: {next_sibling.name}")
                print(f"Text: {next_sibling.get_text().strip()[:200]}")
                next_sibling = next_sibling.find_next_sibling()

    # Also check the page's h3 or dl tags for date headings
    print("\n\n=== Looking for date headings on page ===")
    h3_tags = soup.find_all('h3')
    for h3 in h3_tags[:5]:
        print(f"H3: {h3.get_text().strip()}")
else:
    print("No dt tag found!")
