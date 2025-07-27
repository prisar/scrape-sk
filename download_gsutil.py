import pandas as pd
import concurrent.futures
import subprocess
import os

def parse_file(file_path):
    data = []

    with open(file_path, 'r') as file:
        for line in file:
            subject_code, paper = line.strip().split(' ', 1)
            data.append((subject_code, paper))

    return data

def download_paper(gs_path, local_path):
    gsutil_cp_command = ['gsutil', 'cp', gs_path, local_path]
    subprocess.run(gsutil_cp_command, check=True)

def paper_link(subject_code, paper, yymm):
    v2_gs_path = f"gs://arxiv-dataset/arxiv/arxiv/pdf/{paper.split('.')[0]}/{paper}v2.pdf"
    v1_gs_path = f"gs://arxiv-dataset/arxiv/arxiv/pdf/{paper.split('.')[0]}/{paper}v1.pdf"

    local_path = os.path.join(os.path.expanduser(f'~/Downloads/papers/script/downloads/{subject_code}/'), f'{paper}.pdf')
    # logging.info(f"Downloading {v2_gs_path} or {v1_gs_path} to {local_path}")
    print(f"Downloading {v2_gs_path} or {v1_gs_path} to {local_path}")

    try:
        if subprocess.call(['gsutil', 'ls', v2_gs_path]) == 0:
            download_paper(v2_gs_path, local_path)
        else:
            download_paper(v1_gs_path, local_path)
    except Exception as e:
        logging.error(f"Error downloading {v2_gs_path} or {v1_gs_path}: {e}")


if __name__ == "__main__":

    filename = 'arxiv_28_01_2024_09_54.log'
    yymm = "23" + filename.split('_')[2][:4]

    file_path = 'data' + '/' + filename
    parsed_data = parse_file(file_path)

    df = pd.DataFrame(parsed_data, columns=['Subject Code', 'Paper'])
    filtered_df = df.loc[df['Subject Code'] == 'cs.LG']
    print(filtered_df)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        executor.map(paper_link, filtered_df['Subject Code'], df['Paper'], [yymm] * len(df))
