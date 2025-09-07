import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import time
from google.cloud import storage
import functions_framework

# Initialize GCS client
storage_client = storage.Client()

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

def get_paper_title(paper_id):
    """Get the title of a paper from its abstract page."""
    url = f'https://export.arxiv.org/abs/{paper_id}'
    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    
    try:
        time.sleep(0.2)  # Rate limiting
        response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('h1', class_='title')
        if title_tag:
            return title_tag.text.replace('Title:', '').strip()
    except Exception as e:
        print(f"Error getting title for {paper_id}: {e}")
    return None

def download_topic_pdfs(topic_code, total_entries_past_week, entries):
    """Process a single topic and collect paper information."""
    if int(total_entries_past_week) == 0:
        return 0
    
    page_size = 1000
    url = f'https://export.arxiv.org/list/{topic_code}/pastweek?show={page_size}'
    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    
    try:
        time.sleep(0.1)
        response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        pdf_links = soup.findAll('a', attrs={"title": "Download PDF"})
        pdf_links.reverse()
        
        local_count = 0
        
        for a in pdf_links:
            pdf_link = a.get('href')
            if pdf_link:
                paper_id = pdf_link.split('/')[2]
                paper_title = get_paper_title(paper_id)
                if paper_title:
                    entries.append(f"{topic_code} | {paper_id} | {paper_title}\n")
                    local_count += 1
                else:
                    entries.append(f"{topic_code} | {paper_id} | [Title not found]\n")
                    local_count += 1
                
        return local_count
        
    except Exception as e:
        print(f"Error processing {topic_code}: {e}")
        return 0

def scan_topics():
    """Scan all topics and return list of topics with their paper counts."""
    topic_entries_list = []
    sum_of_papers = 0
    
    for topic_code in topic_codes:
        time.sleep(0.1)
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

@functions_framework.http
def arxiv_scraper(request):
    """HTTP Cloud Function to scrape arXiv papers.
    Args:
        request (flask.Request): The request object.
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
    """
    # Get environment variables
    bucket_name = os.environ.get('BUCKET_NAME', 'your-bucket-name')
    
    try:
        start_time = datetime.now()
        execution_timestamp = datetime.today().strftime("%d_%m_%Y_%H_%M")
        
        # Initialize entries list with header
        entries = ["Topic | Paper ID | Title\n", "-" * 100 + "\n"]
        
        # Get topic entries
        topic_entries = scan_topics()
        
        if not topic_entries:
            return "No topics to process", 400
            
        # Process each topic
        total_downloaded = 0
        for topic_code, count in topic_entries:
            papers_count = download_topic_pdfs(topic_code, count, entries)
            total_downloaded += papers_count
            
        # Upload results to GCS
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(f'arxiv_papers/arxiv_{execution_timestamp}.log')
        blob.upload_from_string(''.join(entries))
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        result = {
            'files_downloaded': total_downloaded,
            'duration': str(duration),
            'log_file': f'gs://{bucket_name}/arxiv_papers/arxiv_{execution_timestamp}.log'
        }
        
        return result, 200
        
    except Exception as error:
        print(f"Function execution error: {error}")
        return str(error), 500
