"""
retrieval_service.py — Async-capable retrieval wrapper.

Exposes both a synchronous `retrieve()` and an async `retrieve_async()`
that runs Pinecone vector search in a thread-pool executor so FastAPI
async endpoints can call it without blocking the event loop.
"""
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from backend.embeddings import embed_texts
from vector_store.pinecone_db import VectorStore

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)

# Shared VectorStore instance (initialised once at import time)
_vector_db = VectorStore()


def _format_docs(raw_docs: list) -> list[str]:
    """Convert Pinecone metadata dicts into tagged context strings."""
    return [f"Source: {doc['source']}\n{doc['text']}" for doc in raw_docs]


def retrieve(query: str, source_filter: str | None = None, top_k: int = 5) -> list[str]:
    """
    Synchronous retrieval.
    Args:
        query: The user question.
        source_filter: Optional prefix to filter by source type
                       (e.g. 'PDF', 'YouTube', 'Image', 'Web Article').
        top_k: Number of results to fetch from Pinecone.
    Returns:
        List of formatted context strings.
    """
    try:
        query_embedding = embed_texts([query])
        raw_docs = _vector_db.search(query, query_embedding, k=top_k)
    except Exception as e:
        logger.error(f"Pinecone search failed: {e}")
        return ["No knowledge found in the database."]

    if not raw_docs:
        return ["No knowledge found in the database."]

    # Optional metadata filtering by source type prefix
    if source_filter and source_filter.upper() != "ALL":
        raw_docs = [doc for doc in raw_docs if source_filter.lower() in doc.get("source", "").lower()]

    if not raw_docs:
        return ["No documents matched the selected source filter."]

    return _format_docs(raw_docs)


async def retrieve_async(query: str, source_filter: str | None = None, top_k: int = 5) -> list[str]:
    """
    Async version of retrieve() — runs in a thread-pool so the event loop
    is never blocked by a synchronous Pinecone HTTP call.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, lambda: retrieve(query, source_filter, top_k)
    )
