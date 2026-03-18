"""
evaluation_service.py — Auto-scores every RAG answer.

Metrics:
  • Relevance (0–1):    Does the answer address the question?
                        Computed as word-overlap between question and answer.
  • Faithfulness (0–1): Score from guardrails_service (no extra LLM call).

This is a lightweight, zero-cost evaluation layer. For production-grade
scoring, this can be swapped for RAGAS or an LLM-as-judge approach.
"""
import re
import logging

logger = logging.getLogger(__name__)

_STOPWORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "with", "are", "was", "be", "has",
    "he", "she", "we", "you", "i", "my", "me", "do", "did",
}


def _meaningful_words(text: str) -> set[str]:
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    return {w for w in words if w not in _STOPWORDS}


def compute_relevance(question: str, answer: str) -> float:
    """
    Measures what fraction of the question's key terms appear in the answer.
    Returns a float between 0.0 and 1.0.
    """
    q_words = _meaningful_words(question)
    if not q_words:
        return 1.0
    a_words = _meaningful_words(answer)
    matched = q_words & a_words
    return round(len(matched) / len(q_words), 3)


def evaluate(question: str, answer: str, faithfulness_score: float) -> dict:
    """
    Run full evaluation for a single QA pair.

    Args:
        question: The user's question.
        answer: The LLM-generated answer.
        faithfulness_score: Score from guardrails_service.check_output()

    Returns:
        dict with keys: relevance, faithfulness, overall
    """
    relevance = compute_relevance(question, answer)
    overall = round((relevance + faithfulness_score) / 2, 3)

    scores = {
        "relevance": relevance,
        "faithfulness": faithfulness_score,
        "overall": overall,
    }

    logger.info(f"Eval scores — {scores}")
    return scores
