import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
API_BASE = os.getenv("OPENAI_API_BASE")

# Model routing: use fast model for simple tasks (routing, grading), slow model for generation
MODEL_NAME = "llama-3.3-70b-versatile"  # Legacy alias used by existing modules
FAST_MODEL = "llama-3.1-8b-instant"
SLOW_MODEL = "llama-3.3-70b-versatile"

# Redis: optional caching layer. App works without it (graceful fallback).
REDIS_URL = os.getenv("REDIS_URL", None)

# Evaluation thresholds
FAITHFULNESS_WARN_THRESHOLD = 0.25  # Flag answers below this score
