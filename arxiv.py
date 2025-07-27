import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
from datetime import datetime
import re

start_time = datetime.now()
topic_codes = [
  ### Computer Science  ###
  'cs.AI',    # Artificial Intelligence
  'cs.CL',    # Computation and Language
  'cs.CV',    # Computer Vision and Pattern Recognition
  'cs.CR',    # Cryptography and Security
  'cs.DC',    # Distributed, Parallel, and Cluster Computing
  'cs.AR',    # Hardware Architecture
  'cs.IT',    # Information Theory
  'cs.LG',    # Machine Learning
  'cs.MA',    # Multiagent Systems
  'cs.NI',    # Networking and Internet Architecture
  'cs.RO',    # Robotics
  'cs.SY',    # Systems and Control

  ### Statistics ###
  'stat.TH',  # Statistics Theory

  ### Electrical Engineering and Systems Science ###
  'eess.AS',  # Audio and Speech Processing
  'eess.IV',  # Image and Video Processing
  'eess.SP',  # Signal Processing

  ### Mathematics ###
  'math.DS',  # Dynamical Systems
  'math.OC',  # Optimization and Control
  'math.PR',  # Probability
  ]

sum_of_papers = 0

def download_topic_pdfs(topic_code, total_entries_past_week):
  """
  download pdf of a particular topic
  """
  url = f'https://export.arxiv.org/list/{topic_code}/pastweek?show={total_entries_past_week}'

  folder_location = f'/Users/apple/Downloads/papers/script/downloads/{topic_code}'
  if not os.path.exists(folder_location):os.mkdir(folder_location)

  response = requests.get(url)
  #print(response.text)

  soup = BeautifulSoup(response.text, 'html.parser')
  #print(soup.title)

  pdf_links = soup.findAll('a', attrs={"title": "Download PDF"})
  print(len(pdf_links))
  for a in pdf_links:
    print(a.get('href'))
    pdf_link = a.get('href')
    filename = os.path.join(folder_location,pdf_link.split('/')[-1] + '.pdf')
    with open(filename, 'wb') as f:
      f.write(requests.get(urljoin(url,pdf_link)).content)


def scan_topics():
  """
  scan topics for previous week papers
  """
  for topic_code in topic_codes: 

    recent_url = f'https://export.arxiv.org/list/{topic_code}/recent'

    response = requests.get(recent_url)

    num_result = re.search('total of (.+?) entries', response.text)
    total_entries_past_week = 0
    if num_result:
      total_entries_past_week = num_result.group(1)
      global sum_of_papers
      sum_of_papers += int(total_entries_past_week)

    print(f'{topic_code} : {total_entries_past_week}')
    download_topic_pdfs(topic_code, total_entries_past_week)

scan_topics()
end_time = datetime.now()
print('Duration: {}'.format(end_time - start_time))
