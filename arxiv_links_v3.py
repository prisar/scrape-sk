import os
from multiprocessing import Pool, cpu_count, Manager
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import re
import time

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

def get_paper_title(paper_id):
    """Get the title of a paper from its abstract page."""
    url = f'https://export.arxiv.org/abs/{paper_id}'
    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    
    try:
        time.sleep(0.2)  # Rate limiting to be polite to arxiv servers
        response = requests.get(url, headers={"User-Agent": useragent}, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title_tag = soup.find('h1', class_='title')
        if title_tag:
            return title_tag.text.replace('Title:', '').strip()
    except Exception as e:
        print(f"Error getting title for {paper_id}: {e}")
    return None

def download_topic_pdfs(args):
    topic_code, total_entries_past_week, shared_counter, shared_lock, log_file_path = args
    
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
        entries = []
        
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
        
        with shared_lock:
            shared_counter.value += local_count
            with open(log_file_path, 'a') as f:
                f.writelines(entries)
                
        return local_count
        
    except Exception as e:
        print(f"Error processing {topic_code}: {e}")
        return 0

def scan_topics():
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

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    log_file_path = f'data/arxiv_{execution_timestamp}.log'
    
    # Create the log file with a header
    with open(log_file_path, 'w') as f:
        f.write("Topic | Paper ID | Title\n")
        f.write("-" * 100 + "\n")
    
    topic_entries = scan_topics()
    
    if not topic_entries:
        print("No topics to process")
        exit(1)
    
    with Manager() as manager:
        shared_counter = manager.Value('i', 0)
        shared_lock = manager.Lock()
        
        args_list = [(topic_code, count, shared_counter, shared_lock, log_file_path) 
                     for topic_code, count in topic_entries]
        
        with Pool(processes=min(cpu_count(), 4)) as pool:  # Reduced processes to prevent rate limiting
            try:
                results = pool.map(download_topic_pdfs, args_list)
                
                end_time = datetime.now()
                total_downloaded = sum(results)
                
                print(f'Files downloaded: {total_downloaded}')
                print(f'Duration: {end_time - start_time}')
                print(f'Log saved to: {log_file_path}')
                
            except Exception as error:
                print(f"Pool execution error: {error}")
