import subprocess

def run_gsutil_command(command):
    try:
        subprocess.run(command, check=True, shell=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

# Example: Copy a file to Google Cloud Storage
source_file = "gs://arxiv-dataset/arxiv/arxiv/pdf/2311/2311.10119v1.pdf"
destination_folder = "data"
command = f"gsutil cp {source_file} {destination_folder}"

run_gsutil_command(command)
