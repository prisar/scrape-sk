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
  'cs.AI',    # Artificial Intelligence
  'cs.CL',    # Computation and Language
  'cs.CC',    # Computational Complexity
  'cs.CE',    # Computational Engineering, Finance, and Science
  'cs.CG',    # Computational Geometry
  'cs.GT',    # Computer Science and Game Theory
  'cs.CV',    # Computer Vision and Pattern Recognition
  'cs.CR',    # Cryptography and Security
  'cs.DS',    # Data Structures and Algorithms
  'cs.DB',    # Databases
  'cs.DM',    # Discrete Mathematics
  'cs.DC',    # Distributed, Parallel, and Cluster Computing
  'cs.FL',    # Formal Languages and Automata Theory
  'cs.GR',    # Graphics
  'cs.AR',    # Hardware Architecture
  'cs.HC',    # Human-Computer Interaction
  'cs.IR',    # Information Retrieval
  'cs.IT',    # Information Theory
  'cs.LO',    # Logic in Computer Science
  'cs.LG',    # Machine Learning
  'cs.MA',    # Multiagent Systems
  'cs.NI',    # Networking and Internet Architecture
  'cs.NA',    # Numerical Analysis
  'cs.OS',    # Operating Systems
  'cs.PF',    # Performance
  'cs.PL',    # Programming Languages
  'cs.RO',    # Robotics
  'cs.SI',    # Social and Information Networks
  'cs.SE',    # Software Engineering
  'cs.SD',    # Sound
  'cs.SC',    # Symbolic Computation
  'cs.SY',    # Systems and Control

  ### Statistics ###
  'stat.AP',  # Applications - Statistics
  'stat.CO',  # Computation - Statistics
  'stat.ML',  # Machine Learning - Statistics
  'stat.TH',  # Statistics Theory

  ### Electrical Engineering and Systems Science ###
  'eess.AS',  # Audio and Speech Processing
  'eess.IV',  # Image and Video Processing
  'eess.SP',  # Signal Processing

  ### Mathematics ###
  'math.DS',  # Dynamical Systems
  'math.OC',  # Optimization and Control
  'math.PR',  # Probability

  ### Physics ###
  'astro-ph.IM',      # Instrumentation and Methods for Astrophysics
  'cond-mat.dis-nn',  # Disordered Systems and Neural Networks
  'nlin.AO',          # Adaptation and Self-Organizing Systems
  'nlin.CD',          # Chaotic Dynamics
  'nlin.SI',          # Exactly Solvable and Integrable Systems
  'physics.app-ph',   # Applied Physics
  'physics.comp-ph',  # Computational Physics
  'physics.data-an',  # Data Analysis, Statistics and Probability
  'physics.ins-det',  # Instrumentation and Detectors
  'physics.med-ph',   # Medical Physics
  'physics.optics',   # Optics

  ### Quantitative Finance ###
  'q-fin.MF', # Mathematical Finance


  ### Economics ###
  'econ.TH',  # Theoretical Economics
  ]

sum_of_papers = 0
download_count = 0

execution_timestamp = datetime.today().strftime("%d_%m_%Y_%H_%M")

def download_topic_pdfs(topic_entry):
  """
  download pdf of a particular topic
  """
  topic_code = topic_entry[0]
  total_entries_past_week = topic_entry[1]
  url = f'https://export.arxiv.org/list/{topic_code}/pastweek?show={total_entries_past_week}'

  time.sleep(0.1)
  useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
  response = requests.get(url, headers={"User-Agent": useragent})
  soup = BeautifulSoup(response.text, 'html.parser')

  pdf_links = soup.findAll('a', attrs={"title": "Download PDF"})
  pdf_links.reverse()
  for a in pdf_links:
    pdf_link = a.get('href')

    lock.acquire()
    global download_count
    download_count = download_count + 1
    # print(f"{time.strftime('%H:%M:%S')} {download_count} {topic_code} {a.get('href')}")
    with open(f'data/arxiv_{execution_timestamp}.log', 'a') as the_file:
      the_file.write(f"{topic_code} {a.get('href').split('/')[2]}\n")
    lock.release()

lock = threading.Lock()

def scan_topics():
  """
  scan topics for previous week papers
  """

  topic_entries_list = []
  for topic_code in topic_codes: 
    time.sleep(0.1)
    recent_url = f'https://export.arxiv.org/list/{topic_code}/recent'

    useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
    response = requests.get(recent_url, headers={"User-Agent": useragent})

    num_result = re.search('Total of (.+?) entries', response.text) or re.search('total of (.+?) entries', response.text)
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
  time.sleep(0.1)
  pool = Pool(processes=cpu_count())
  try:
    pool.map(download_topic_pdfs, topic_entries)
    end_time = datetime.now()
    # print(f'files downloaded {download_count}')
    print('Duration: {}'.format(end_time - start_time))
  except Exception as error:
    print(error) 

