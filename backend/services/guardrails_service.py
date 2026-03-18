"""
guardrails_service.py — Input sanitization + output grounding checks.

Input Guardrails:
  Detects common prompt injection patterns and sanitizes special characters.

Output Guardrails:
  Computes a lightweight faithfulness score by checking whether key noun
  phrases from the generated answer appear in the retrieved context.
  Flags answers below FAITHFULNESS_WARN_THRESHOLD.
"""
import re
import logging
from backend.config import FAITHFULNESS_WARN_THRESHOLD

logger = logging.getLogger(__name__)

# ── Prompt injection patterns ──────────────────────────────────────
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"you\s+are\s+now\s+[a-zA-Z]",
    r"act\s+as\s+(if\s+you\s+are|a)\s+",
    r"forget\s+(everything|all)",
    r"your\s+(new\s+)?instructions?\s+are",
    r"system\s*:\s*",      # Inline system prompt injection
    r"</?(s|system|prompt|context)>",
]

_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


def check_input(text: str) -> tuple[bool, str]:
    """
    Validate user input.
    Returns:
        (is_safe, sanitized_text)
        is_safe = False means a prompt injection was detected.
    """
    if _INJECTION_RE.search(text):
        logger.warning(f"Prompt injection detected in input: '{text[:80]}...'")
        return False, text

    # Sanitize: remove null bytes and excessive whitespace
    sanitized = re.sub(r"\x00", "", text)
    sanitized = re.sub(r"\s{4,}", "   ", sanitized).strip()
    return True, sanitized


def check_output(answer: str, context: str) -> tuple[float, bool]:
    """
    Compute a simple faithfulness score for the generated answer.

    Strategy:
      Extract significant words (≥5 chars) from the answer, then check
      what fraction of them appear in the context. This serves as a
      lightweight proxy for hallucination detection without an extra LLM call.

    Returns:
        (faithfulness_score [0.0–1.0], is_flagged)
        is_flagged = True means the answer may contain hallucinations.
    """
    # Extract meaningful words from the answer (ignore common stopwords)
    stopwords = {"about", "after", "being", "could", "every", "first", "from",
                 "given", "their", "there", "these", "those", "through", "under",
                 "which", "while", "would"}

    answer_words = re.findall(r"\b[a-zA-Z]{5,}\b", answer.lower())
    significant = [w for w in answer_words if w not in stopwords]

    if not significant:
        return 1.0, False  # Nothing to verify

    context_lower = context.lower()
    matched = sum(1 for w in significant if w in context_lower)
    score = matched / len(significant)

    is_flagged = score < FAITHFULNESS_WARN_THRESHOLD
    if is_flagged:
        logger.warning(f"Low faithfulness score: {score:.2f} — possible hallucination detected.")

    return round(score, 3), is_flagged
