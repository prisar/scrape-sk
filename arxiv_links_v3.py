import os
from multiprocessing import Pool, cpu_count, Manager
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import re
import time
import csv

start_time = datetime.now()

topic_codes = [
    'cs.AI', 'cs.CL', 'cs.CC', 'cs.CE', 'cs.CG', 'cs.GT', 'cs.CV', 'cs.CR',
    'cs.DS', 'cs.DB', 'cs.DM', 'cs.DC', 'cs.FL', 'cs.GR', 'cs.AR', 'cs.HC',
    'cs.IR', 'cs.IT', 'cs.LO', 'cs.LG', 'cs.MA', 'cs.NI', 'cs.NA', 'cs.OS',
    'cs.PF', 'cs.PL', 'cs.RO', 'cs.SI', 'cs.SE', 'cs.SD', 'cs.SC', 'cs.SY',
    'stat.AP', 'stat.CO', 'stat.ML', 'stat.TH',
    'eess.AS', 'eess.IV', 'eess.SP',
    'math.DS', 'math.OC', 'math.PR',
    'astro-ph.IM', 'cond-mat.dis-nn', 'nlin.AO', 'nlin.CD', 'nlin.SI',
    'physics.app-ph', 'physics.comp-ph', 'physics.data-an', 'physics.ins-det',
    'physics.med-ph', 'physics.optics',
    'q-fin.MF', 'econ.TH'
]

execution_timestamp = datetime.today().strftime("%d_%m_%Y_%H_%M")

def download_topic_pdfs(args):
    topic_code, total_entries_past_week, shared_counter, shared_lock, log_file_path = args

    if int(total_entries_past_week) == 0:
        return 0

    page_size = 1000
    url = f'https://export.arxiv.org/list/{topic_code}/recent?show={page_size}'

    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"

    try:
        response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find ALL articles dl elements (there can be multiple, one per date)
        articles_dls = soup.find_all('dl', id='articles')
        if not articles_dls:
            print(f"No articles found for {topic_code}")
            return 0

        local_count = 0
        entries = []

        # Iterate through each dl element (each represents a different date)
        for articles_dl in articles_dls:
            current_date = "[Date not found]"

            # Iterate through all children of this dl element
            for element in articles_dl.children:
                # Skip text nodes
                if not hasattr(element, 'name'):
                    continue

                # Check if it's an h3 tag (date header)
                if element.name == 'h3':
                    date_text = element.get_text().strip()
                    # Extract date from format like "Mon, 15 Dec 2025 (showing 101 of 101 entries )"
                    date_match = re.search(r'(\w+,\s+\d{1,2}\s+\w+\s+\d{4})', date_text)
                    if date_match:
                        current_date = date_match.group(1)
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
                    local_count += 1

        # Write all entries at once with lock
        if entries:
            with shared_lock:
                shared_counter.value += local_count
                with open(log_file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(entries)

        return local_count

    except Exception as e:
        print(f"Error processing {topic_code}: {e}")
        return 0

def scan_topics():
    topic_entries_list = []
    sum_of_papers = 0

    for topic_code in topic_codes:
        recent_url = f'https://export.arxiv.org/list/{topic_code}/recent'

        useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"

        try:
            response = requests.get(recent_url, headers={"User-Agent": useragent}, timeout=30)
            response.raise_for_status()

            num_result = re.search(r'Total of (\d+) entries', response.text, re.IGNORECASE)
            total_entries_past_week = 0

            if num_result:
                total_entries_past_week = int(num_result.group(1))
                sum_of_papers += total_entries_past_week

            print(f'{topic_code} : {total_entries_past_week}')
            topic_entries_list.append((topic_code, str(total_entries_past_week)))

        except Exception as e:
            print(f"Error scanning {topic_code}: {e}")
            topic_entries_list.append((topic_code, "0"))

    print(f'sum of papers {sum_of_papers}')
    return topic_entries_list

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    csv_file_path = f'data/arxiv_{execution_timestamp}.csv'

    # Create the CSV file with headers
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Paper PDF URL', 'Topic', 'Published Date'])

    topic_entries = scan_topics()

    if not topic_entries:
        print("No topics to process")
        exit(1)

    with Manager() as manager:
        shared_counter = manager.Value('i', 0)
        shared_lock = manager.Lock()

        args_list = [(topic_code, count, shared_counter, shared_lock, csv_file_path)
                     for topic_code, count in topic_entries]

        with Pool(processes=min(cpu_count(), 8)) as pool:  # Increased processes for better performance
            try:
                results = pool.map(download_topic_pdfs, args_list)

                end_time = datetime.now()
                total_downloaded = sum(results)

                print(f'Papers processed: {total_downloaded}')
                print(f'Duration: {end_time - start_time}')
                print(f'CSV saved to: {csv_file_path}')

            except Exception as error:
                print(f"Pool execution error: {error}")
