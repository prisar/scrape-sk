import os
from multiprocessing import Pool, cpu_count, Manager
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus
from datetime import datetime
import re
import time
import csv

start_time = datetime.now()

# Define your search terms here
search_terms = [
    'PRM',
    'process reward model',
    'reinforcement learning from human feedback',
    'RLHF',
    'chain of thought',
    'constitutional AI',
]

# Configuration for the search
search_config = {
    'field': 'all',  # Options: 'all', 'title', 'abstract', 'author', 'comments', etc.
    'classification': 'computer_science',  # 'computer_science', 'physics', 'mathematics', etc.
    'date_filter': 'past_12',  # 'past_12', 'past_6', 'past_3', 'all_dates', etc.
    'size': 200,  # Number of results per page
    'order': '-announced_date_first',  # Sort order
}

execution_timestamp = datetime.today().strftime("%d_%m_%Y_%H_%M")

def build_search_url(term, start=0):
    """Build the ArXiv advanced search URL for a given term."""
    base_url = "https://arxiv.org/search/advanced"

    params = {
        'advanced': '',
        'terms-0-operator': 'AND',
        'terms-0-term': term,
        'terms-0-field': search_config['field'],
        'classification-include_cross_list': 'include',
        'date-filter_by': search_config['date_filter'],
        'date-year': '',
        'date-from_date': '',
        'date-to_date': '',
        'date-date_type': 'submitted_date',
        'abstracts': 'hide',
        'size': search_config['size'],
        'order': search_config['order'],
        'start': start
    }

    # Add classification
    if search_config['classification'] == 'computer_science':
        params['classification-computer_science'] = 'y'
        params['classification-physics_archives'] = 'all'

    # Build query string manually to match the format
    query_parts = []
    for key, value in params.items():
        query_parts.append(f"{key}={quote_plus(str(value))}")

    return f"{base_url}?{'&'.join(query_parts)}"

def extract_paper_info(result_item):
    """Extract paper information from a search result item."""
    try:
        # Extract title
        title_tag = result_item.find('p', class_='title')
        title = title_tag.get_text().strip() if title_tag else "[Title not found]"

        # Extract paper ID from the link
        link_tag = result_item.find('p', class_='list-title').find('a') if result_item.find('p', class_='list-title') else None
        if not link_tag:
            return None

        paper_url = link_tag.get('href', '')
        paper_id_match = re.search(r'abs/(\d+\.\d+)', paper_url)
        if not paper_id_match:
            return None

        paper_id = paper_id_match.group(1)
        pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"

        # Extract date
        date_tag = result_item.find('p', class_='is-size-7')
        date_text = date_tag.get_text().strip() if date_tag else "[Date not found]"

        # Parse date from format like "Submitted 15 December, 2024"
        date_match = re.search(r'Submitted\s+(\d{1,2}\s+\w+,?\s+\d{4})', date_text)
        published_date = date_match.group(1) if date_match else date_text

        # Extract primary subject
        subjects_tag = result_item.find('p', class_='is-size-7')
        subject = search_config['classification'] if subjects_tag else "[Subject not found]"
        if subjects_tag:
            subject_match = re.search(r'([a-z\-]+\.[A-Z]+)', subjects_tag.get_text())
            if subject_match:
                subject = subject_match.group(1)

        return [title, '', pdf_url, subject, published_date]

    except Exception as e:
        print(f"Error extracting paper info: {e}")
        return None

def search_arxiv_term(args):
    """Search ArXiv for a specific term and extract papers."""
    search_term, shared_counter, shared_lock, log_file_path = args

    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"

    try:
        url = build_search_url(search_term, start=0)
        print(f"Searching for: {search_term}")

        response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find total number of results
        total_results_tag = soup.find('h1', class_='title')
        total_results = 0
        if total_results_tag:
            total_match = re.search(r'of\s+([\d,]+)\s+results', total_results_tag.get_text())
            if total_match:
                total_results = int(total_match.group(1).replace(',', ''))

        print(f"Found {total_results} results for '{search_term}'")

        if total_results == 0:
            return 0

        local_count = 0
        entries = []

        # Process first page
        results = soup.find_all('li', class_='arxiv-result')
        for result_item in results:
            paper_info = extract_paper_info(result_item)
            if paper_info:
                # Add search term to the entry
                paper_info.append(search_term)
                entries.append(paper_info)
                local_count += 1

        # Calculate if we need to fetch more pages
        pages_needed = min((total_results // search_config['size']) + 1, 5)  # Limit to 5 pages max

        # Fetch additional pages if needed
        for page in range(1, pages_needed):
            start_index = page * search_config['size']
            if start_index >= total_results:
                break

            print(f"Fetching page {page + 1} for '{search_term}'...")
            time.sleep(1)  # Be respectful to the server

            url = build_search_url(search_term, start=start_index)
            response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            results = soup.find_all('li', class_='arxiv-result')
            for result_item in results:
                paper_info = extract_paper_info(result_item)
                if paper_info:
                    paper_info.append(search_term)
                    entries.append(paper_info)
                    local_count += 1

        # Write all entries at once with lock
        if entries:
            with shared_lock:
                shared_counter.value += local_count
                with open(log_file_path, 'a', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerows(entries)

        print(f"Completed '{search_term}': {local_count} papers extracted")
        return local_count

    except Exception as e:
        print(f"Error processing '{search_term}': {e}")
        return 0

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    csv_file_path = f'data/arxiv_search_{execution_timestamp}.csv'

    # Create the CSV file with headers
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Title', 'Status', 'Paper PDF URL', 'Topic', 'Published Date', 'Search Term'])

    if not search_terms:
        print("No search terms to process")
        exit(1)

    with Manager() as manager:
        shared_counter = manager.Value('i', 0)
        shared_lock = manager.Lock()

        args_list = [(term, shared_counter, shared_lock, csv_file_path)
                     for term in search_terms]

        # Use fewer processes to avoid overwhelming the server
        with Pool(processes=min(cpu_count(), 4)) as pool:
            try:
                results = pool.map(search_arxiv_term, args_list)

                end_time = datetime.now()
                total_downloaded = sum(results)

                print(f'\nPapers processed: {total_downloaded}')
                print(f'Duration: {end_time - start_time}')
                print(f'CSV saved to: {csv_file_path}')

            except Exception as error:
                print(f"Pool execution error: {error}")
