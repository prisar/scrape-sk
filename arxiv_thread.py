import threading
from multiprocessing import Pool, cpu_count
import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from datetime import datetime
import re
import time

start_time = datetime.now()

topic_codes = [
  ### Computer Science  ###
  # 'cs.AI',    # Artificial Intelligence
  # 'cs.CL',    # Computation and Language
  # 'cs.CV',    # Computer Vision and Pattern Recognition
  # 'cs.CR',    # Cryptography and Security
  # 'cs.DC',    # Distributed, Parallel, and Cluster Computing
  # 'cs.AR',    # Hardware Architecture
  # 'cs.IT',    # Information Theory
  'cs.LG',    # Machine Learning
  # 'cs.MA',    # Multiagent Systems
  # 'cs.NI',    # Networking and Internet Architecture
  # 'cs.RO',    # Robotics
  # 'cs.SY',    # Systems and Control

  # ### Statistics ###
  # 'stat.TH',  # Statistics Theory

  # ### Electrical Engineering and Systems Science ###
  # 'eess.AS',  # Audio and Speech Processing
  # 'eess.IV',  # Image and Video Processing
  # 'eess.SP',  # Signal Processing

  # ### Mathematics ###
  # 'math.DS',  # Dynamical Systems
  # 'math.OC',  # Optimization and Control
  # 'math.PR',  # Probability
  ]

sum_of_papers = 0
download_count = 0

def download_topic_pdfs(topic_entry):
  """
  download pdf of a particular topic
  """
  topic_code = topic_entry[0]
  total_entries_past_week = topic_entry[1]
  url = f'https://export.arxiv.org/list/{topic_code}/pastweek?show={total_entries_past_week}'

  folder_location = f'/Users/apple/Downloads/papers/script/downloads/{topic_code}'
  if not os.path.exists(folder_location):os.mkdir(folder_location)

  time.sleep(0.5)
  useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
  response = requests.get(url, headers={"User-Agent": useragent})
  soup = BeautifulSoup(response.text, 'html.parser')

  pdf_links = soup.findAll('a', attrs={"title": "Download PDF"})
  pdf_links.reverse()
  for a in pdf_links:
    pdf_link = a.get('href')
    filename = os.path.join(folder_location,pdf_link.split('/')[-1] + '.pdf')
    # print(len(pdf_links))

    # if file does not exists or file size equal to zero
    if not os.path.exists(filename) or not (os.path.getsize(filename) > 10240):
      time.sleep(0.25)

      lock.acquire()
      global download_count
      download_count = download_count + 1
      print(f"{time.strftime('%H:%M:%S')} {download_count} {topic_code} {a.get('href')}")
      lock.release()

      with open(filename, 'wb') as f:
        f.write(requests.get(urljoin(url,pdf_link)).content)

lock = threading.Lock()

def scan_topics():
  """
  scan topics for previous week papers
  """

  topic_entries_list = []
  for topic_code in topic_codes: 
    time.sleep(2)
    recent_url = f'https://export.arxiv.org/list/{topic_code}/recent'

    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    response = requests.get(recent_url, headers={"User-Agent": useragent})

    num_result = re.search('total of (.+?) entries', response.text)
    total_entries_past_week = 0
    if num_result:
      total_entries_past_week = num_result.group(1)
      global sum_of_papers
      sum_of_papers += int(total_entries_past_week)

    print(f'{topic_code} : {total_entries_past_week}')
    topic_entries_list.append((topic_code, total_entries_past_week))    

  print(f'sum of papers {sum_of_papers}')
  return topic_entries_list

if __name__ == '__main__':
  topic_entries = scan_topics()
  time.sleep(1)
  pool = Pool(processes=cpu_count())
  try:
    pool.map(download_topic_pdfs, topic_entries)
    end_time = datetime.now()
    # print(f'files downloaded {download_count}')
    print('Duration: {}'.format(end_time - start_time))
  except Exception as error:
    print(error) 

