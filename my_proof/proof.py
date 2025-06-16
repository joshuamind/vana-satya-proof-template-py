import json
import logging
import os
from typing import Dict, Any

import requests

from my_proof.models.proof_response import ProofResponse


class Proof:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.proof_response = ProofResponse(dlp_id=config['dlp_id'])

    def generate(self) -> ProofResponse:
        """Generate proofs for all input files."""
        logging.info("Starting proof generation")

        # Iterate through files and calculate data validity
        account_email = None
        total_score = 0

         # 假设 input_dir 下只有一个文件
        input_filenames = [
            f for f in os.listdir(self.config['input_dir'])
            if f.startswith('vana_') and os.path.isfile(os.path.join(self.config['input_dir'], f))
        ]
        
        if not input_filenames:
            raise FileNotFoundError(f"No input files found in {self.config['input_dir']}")

        input_file_path = os.path.join(self.config['input_dir'], input_filenames[0])

        try:
            with open(input_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                wallet_address = data.get('walletAddress')
                file_hash = data.get('fileHash')
                logging.info(f"Loaded wallet: {wallet_address}, fileHash: {file_hash}")
                result = verify_wallet(wallet_address, file_hash)
                logging.info(f"Verification result: {result}")
        except Exception as e:
            logging.error(f"Error reading input file: {e}")
            raise e
            

        # Calculate proof-of-contribution scores: https://docs.vana.org/vana/core-concepts/key-elements/proof-of-contribution/example-implementation
        self.proof_response.ownership = 1.0 # Does the data belong to the user? Or is it fraudulent?
        self.proof_response.quality = 1.0   # How high quality is the data?
        self.proof_response.authenticity = 1.0  # How authentic is the data is (ie: not tampered with)? (Not implemented here)
        self.proof_response.uniqueness = 1.0  # How unique is the data relative to other datasets? (Not implemented here)

        # Calculate overall score and validity
        self.proof_response.score = 1.0 if result.get("data") else 0.0
        self.proof_response.valid = result.get("data",False)

        # Additional (public) properties to include in the proof about the data
        self.proof_response.attributes = {
            'total_score': total_score,
        }

        # Additional metadata about the proof, written onchain
        self.proof_response.metadata = {
            'dlp_id': self.config['dlp_id'],
        }

        return self.proof_response


def fetch_random_number() -> float:
    """Demonstrate HTTP requests by fetching a random number from random.org."""
    try:
        response = requests.get('https://www.random.org/decimal-fractions/?num=1&dec=2&col=1&format=plain&rnd=new')
        return float(response.text.strip())
    except requests.RequestException as e:
        logging.warning(f"Error fetching random number: {e}. Using local random.")
        return __import__('random').random()


def verify_wallet(wallet_address: str, file_hash: str) -> dict:
    url = 'https://mcp-api.mindnetwork.io/health-hub/verify/check'
    payload = {
        'walletAddress': wallet_address,
        'fileHash': file_hash
    }

    response = requests.post(url, json=payload)
    response.raise_for_status()  
    return response.json()