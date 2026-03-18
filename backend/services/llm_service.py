"""
llm_service.py — Centralised LLM call layer with:
  • Dynamic model routing (simple → fast model, complex → slow model)
  • Retry with exponential backoff (via tenacity)
  • Fallback model if primary fails
"""
import logging
import time
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from backend.config import GROQ_API_KEY, API_BASE, FAST_MODEL, SLOW_MODEL

logger = logging.getLogger(__name__)

client = OpenAI(api_key=GROQ_API_KEY, base_url=API_BASE)

# Query length threshold: below this → fast model, above → slow model
_COMPLEXITY_THRESHOLD = 80  # characters


def _select_model(question: str, force_fast: bool = False, force_slow: bool = False) -> str:
    """Dynamically choose the LLM model based on query complexity."""
    if force_fast:
        return FAST_MODEL
    if force_slow:
        return SLOW_MODEL
    # Heuristic: short or simple questions → fast model
    if len(question) < _COMPLEXITY_THRESHOLD:
        return FAST_MODEL
    return SLOW_MODEL


def _call_with_retry(model: str, messages: list, temperature: float = 0.2, max_tokens: int = 1024) -> str:
    """Make an LLM call with up to 3 retries and exponential backoff."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content
        except RateLimitError as e:
            wait = 2 ** attempt
            logger.warning(f"Rate limit hit (attempt {attempt+1}), retrying in {wait}s...")
            time.sleep(wait)
        except APITimeoutError as e:
            wait = 2 ** attempt
            logger.warning(f"API timeout (attempt {attempt+1}), retrying in {wait}s...")
            time.sleep(wait)
        except APIError as e:
            logger.error(f"Groq API error: {e}")
            break  # Non-retryable
    raise RuntimeError(f"LLM call failed after {max_retries} attempts with model '{model}'.")


def generate_answer(context: str, question: str) -> tuple[str, str]:
    """
    Generate a grounded answer from context.
    Returns (answer_text, model_used).
    Falls back to FAST_MODEL if SLOW_MODEL fails.
    """
    prompt = f"""Use the following context to answer the question. Be concise and factual.
If the context does not contain enough information, say so clearly.

Context:
{context}

Question:
{question}"""

    messages = [{"role": "user", "content": prompt}]
    model = _select_model(question)

    try:
        answer = _call_with_retry(model, messages)
        return answer, model
    except RuntimeError:
        logger.warning(f"Primary model '{model}' failed, falling back to '{FAST_MODEL}'...")
        fallback = FAST_MODEL if model == SLOW_MODEL else SLOW_MODEL
        try:
            answer = _call_with_retry(fallback, messages)
            return answer, f"{fallback} (fallback)"
        except RuntimeError as e:
            raise RuntimeError(f"All LLM models failed: {e}")


def generate_direct(question: str) -> tuple[str, str]:
    """
    Answer a direct/general question without any retrieved context.
    Uses fast model for speed.
    """
    messages = [{"role": "user", "content": question}]
    try:
        answer = _call_with_retry(FAST_MODEL, messages)
        return answer, FAST_MODEL
    except RuntimeError as e:
        raise RuntimeError(f"Direct LLM call failed: {e}")


def classify(prompt: str, valid_outputs: list[str]) -> str:
    """
    Low-cost classification call — always uses the fast model.
    Returns one of `valid_outputs` or the first as fallback.
    """
    try:
        response = client.chat.completions.create(
            model=FAST_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10,
        )
        decision = response.choices[0].message.content.strip().upper()
        if decision in [v.upper() for v in valid_outputs]:
            return decision
    except Exception as e:
        logger.warning(f"Classify call failed: {e}")
    return valid_outputs[0]
