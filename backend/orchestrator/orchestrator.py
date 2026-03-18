"""
orchestrator.py — Central coordinator for all query handling.

Flow per query:
  1. Cache check → return immediately if hit
  2. Input guardrails (injection detection)
  3. Agent routing (VECTOR_SEARCH | DATA_ANALYST | DIRECT_CHAT)
  4. Async Retrieval (for VECTOR_SEARCH path)
  5. Self-RAG relevance filter
  6. LLM Generation (dynamic model selection + retry)
  7. Output guardrails (faithfulness check)
  8. Evaluation scoring
  9. Cache write
  10. Return answer + rich metadata
"""
import asyncio
import time
import logging
from backend.services import cache_service, llm_service, retrieval_service
from backend.services import guardrails_service, evaluation_service

logger = logging.getLogger(__name__)

# Lazy imports for agent — preserves backward compatibility
from backend.agent import route_query, check_relevance


async def handle_query(
    question: str,
    data_mode: bool = False,
    source_filter: str | None = None,
) -> dict:
    """
    Full async pipeline. Returns:
        {
            "answer": str,
            "metadata": {
                "route": str,
                "model_used": str,
                "cache_hit": bool,
                "latency_ms": int,
                "self_rag": str,
                "guardrail_warning": bool,
                "eval": {"relevance": float, "faithfulness": float, "overall": float},
            }
        }
    """
    start_time = time.time()

    # ── 1. Cache check ─────────────────────────────────────────────
    cache_key = f"{question}::{source_filter or 'all'}"
    cached_answer, cached_meta = cache_service.get_cached_answer(cache_key)
    if cached_answer:
        elapsed = int((time.time() - start_time) * 1000)
        cached_meta["cache_hit"] = True
        cached_meta["latency_ms"] = elapsed
        logger.info(f"Cache HIT for query: '{question[:50]}'")
        return {"answer": cached_answer, "metadata": cached_meta}

    # ── 2. Input guardrails ────────────────────────────────────────
    is_safe, clean_question = guardrails_service.check_input(question)
    if not is_safe:
        meta = {
            "route": "BLOCKED",
            "model_used": "none",
            "cache_hit": False,
            "latency_ms": int((time.time() - start_time) * 1000),
            "guardrail_warning": True,
            "self_rag": "N/A",
            "eval": {"relevance": 0.0, "faithfulness": 0.0, "overall": 0.0},
        }
        return {
            "answer": "⚠️ Your message was flagged by the security guardrail and blocked. Please rephrase your question.",
            "metadata": meta,
        }

    # ── 3. Agent routing ───────────────────────────────────────────
    # Check routing cache first
    cached_route = cache_service.get_routing(clean_question)
    if cached_route:
        route = cached_route
    else:
        route = await asyncio.get_event_loop().run_in_executor(
            None, lambda: route_query(clean_question)
        )
        if data_mode:
            route = "DATA_ANALYST"
        cache_service.set_routing(clean_question, route)

    answer = ""
    model_used = "none"
    context_used = ""
    self_rag_info = "N/A"

    # ── 4. Handle DATA_ANALYST route ─────────────────────────────
    if route == "DATA_ANALYST":
        from backend.data_analyst import answer_data_question
        answer = await asyncio.get_event_loop().run_in_executor(
            None, lambda: answer_data_question(clean_question)
        )
        model_used = "data_analyst"

    # ── 5. Handle DIRECT_CHAT route ──────────────────────────────
    elif route == "DIRECT_CHAT":
        answer, model_used = await asyncio.get_event_loop().run_in_executor(
            None, lambda: llm_service.generate_direct(clean_question)
        )

    # ── 6. Handle VECTOR_SEARCH route (Self-RAG) ─────────────────
    else:
        # Async retrieval
        raw_docs = await retrieval_service.retrieve_async(clean_question, source_filter)

        if not raw_docs or "No knowledge" in raw_docs[0]:
            self_rag_info = "No documents found in knowledge base."
            answer = "I don't have any specific information about this in my knowledge base."
            model_used = "none"
        else:
            # Self-RAG: relevance filter (run checks in parallel via asyncio.gather)
            async def _check(doc):
                return await asyncio.get_event_loop().run_in_executor(
                    None, lambda: check_relevance(clean_question, doc)
                )

            relevance_flags = await asyncio.gather(*[_check(doc) for doc in raw_docs[:5]])
            valid_docs = [doc for doc, ok in zip(raw_docs[:5], relevance_flags) if ok]

            self_rag_info = f"Passed {len(valid_docs)}/{min(len(raw_docs), 5)} relevance checks."

            if not valid_docs:
                answer = "I searched my knowledge base but the retrieved content wasn't directly relevant. Please try rephrasing your question."
                model_used = "none"
            else:
                context_used = "\n\n".join(valid_docs)
                answer, model_used = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: llm_service.generate_answer(context_used, clean_question)
                )

    # ── 7. Output guardrails ──────────────────────────────────────
    relevant_context = context_used if context_used else answer  # Use answer as context proxy for non-RAG routes
    faithfulness_score, guardrail_flagged = guardrails_service.check_output(answer, relevant_context)

    # ── 8. Evaluation ──────────────────────────────────────────────
    eval_scores = evaluation_service.evaluate(clean_question, answer, faithfulness_score)

    # ── 9. Cache write ────────────────────────────────────────────
    elapsed = int((time.time() - start_time) * 1000)
    metadata = {
        "route": route,
        "model_used": model_used,
        "cache_hit": False,
        "latency_ms": elapsed,
        "self_rag": self_rag_info,
        "guardrail_warning": guardrail_flagged,
        "eval": eval_scores,
    }
    cache_service.set_answer(cache_key, answer, metadata, ttl=1800)

    return {"answer": answer, "metadata": metadata}


def handle_query_sync(
    question: str,
    data_mode: bool = False,
    source_filter: str | None = None,
) -> dict:
    """
    Synchronous wrapper around handle_query() for use in sync FastAPI endpoints
    (those not declared async). Creates a new event loop if needed.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already inside a running loop (e.g. Starlette async context)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run, handle_query(question, data_mode, source_filter)
                )
                return future.result()
        else:
            return loop.run_until_complete(handle_query(question, data_mode, source_filter))
    except RuntimeError:
        return asyncio.run(handle_query(question, data_mode, source_filter))
