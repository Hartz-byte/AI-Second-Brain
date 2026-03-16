import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")
MODEL_NAME = "llama-3.3-70b-versatile"
