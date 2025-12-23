import requests
from bs4 import BeautifulSoup
import re
import csv
from datetime import datetime

# Test with just one topic
topic_code = 'cs.AI'
page_size = 1000
url = f'https://export.arxiv.org/list/{topic_code}/recent?show={page_size}'

useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"

print(f"Fetching {url}...")
response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
print(f"Status code: {response.status_code}")

soup = BeautifulSoup(response.text, 'html.parser')

# Find the articles dl element
articles_dl = soup.find('dl', id='articles')
if not articles_dl:
    print("No articles dl found!")
    exit(1)

print("Found articles dl element")

entries = []
current_date = "[Date not found]"

# Iterate through all children of the dl element
for element in articles_dl.children:
    # Skip text nodes
    if not hasattr(element, 'name'):
        continue

    # Check if it's an h3 tag (date header)
    if element.name == 'h3':
        date_text = element.get_text().strip()
        print(f"Found date header: {date_text}")
        # Extract date from format like "Mon, 15 Dec 2025 (showing 101 of 101 entries )"
        date_match = re.search(r'(\w+,\s+\d{1,2}\s+\w+\s+\d{4})', date_text)
        if date_match:
            current_date = date_match.group(1)
            print(f"Extracted date: {current_date}")
        continue

    # Check if it's a dt tag (paper entry)
    if element.name == 'dt':
        # Find the PDF link in the dt tag
        pdf_link_tag = element.find('a', attrs={"title": "Download PDF"})
        if not pdf_link_tag:
            continue

        pdf_link = pdf_link_tag.get('href')
        if not pdf_link:
            continue

        paper_id = pdf_link.split('/')[2]
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

        # Find the title in the next dd sibling
        dd = element.find_next_sibling('dd')
        if dd:
            title_div = dd.find('div', class_='list-title')
            if title_div:
                title = title_div.get_text().replace('Title:', '').strip()
            else:
                title = "[Title not found]"
        else:
            title = "[Title not found]"

        entries.append([title, pdf_url, topic_code, current_date])

print(f"\nTotal papers found: {len(entries)}")
print("\nFirst 5 papers:")
for i, entry in enumerate(entries[:5]):
    print(f"\n{i+1}. Title: {entry[0][:80]}...")
    print(f"   URL: {entry[1]}")
    print(f"   Date: {entry[3]}")

print("\nLast 5 papers:")
for i, entry in enumerate(entries[-5:], len(entries)-4):
    print(f"\n{i}. Title: {entry[0][:80]}...")
    print(f"   URL: {entry[1]}")
    print(f"   Date: {entry[3]}")

# Save to test CSV
test_csv = 'test_dates.csv'
with open(test_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Title', 'Paper PDF URL', 'Topic', 'Published Date'])
    writer.writerows(entries)

print(f"\nSaved test results to {test_csv}")
