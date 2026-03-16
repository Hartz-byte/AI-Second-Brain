import requests
import os
import time
from dotenv import load_dotenv
import numpy as np

load_dotenv()

# We use the same model but hosted on Hugging Face's free Inference API
MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
API_URL = f"https://router.huggingface.co/models/{MODEL_ID}"
HF_TOKEN = os.getenv("HF_TOKEN")

def embed_texts(texts):
    # This function handles both single strings and lists of strings
    is_single = isinstance(texts, str)
    payload = {"inputs": [texts] if is_single else texts, "options": {"wait_for_model": True}}
    
    headers = {}
    if HF_TOKEN:
        headers["Authorization"] = f"Bearer {HF_TOKEN}"

    for _ in range(3):  # Simple retry logic
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            embeddings = response.json()
            return np.array(embeddings[0]) if is_single else np.array(embeddings)
        elif response.status_code == 503: # Model loading
            time.sleep(5)
            continue
        else:
            raise Exception(f"HF API Error: {response.text}")
            
    raise Exception("Hugging Face API timed out.")
