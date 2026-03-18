"""
streaming.py — SSE streaming endpoint for real-time token delivery.

Registers a /ask_stream route that streams Groq tokens to the frontend
via Server-Sent Events (text/event-stream).
"""
import json
import asyncio
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from openai import OpenAI
from backend.config import GROQ_API_KEY, API_BASE
from backend.services.guardrails_service import check_input
from backend.agent import route_query
from backend.services.retrieval_service import retrieve_async
from backend.agent import check_relevance
from backend.config import SLOW_MODEL, FAST_MODEL

logger = logging.getLogger(__name__)
router = APIRouter()

_client = OpenAI(api_key=GROQ_API_KEY, base_url=API_BASE)


async def _stream_from_groq(prompt: str, model: str):
    """Async generator that yields SSE-formatted chunks from Groq streaming."""
    try:
        stream = _client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            max_tokens=1024,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield f"data: {json.dumps({'token': delta})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
        yield "data: [DONE]\n\n"


@router.post("/ask_stream")
async def ask_stream(data: dict):
    """
    Streaming version of /ask. Returns tokens progressively via SSE.
    The frontend consumes this with a fetch() + ReadableStream reader.
    """
    question = data.get("question", "").strip()
    source_filter = data.get("source_filter", None)

    # Input guardrail
    is_safe, clean_q = check_input(question)
    if not is_safe:
        async def blocked():
            yield "data: " + json.dumps({"token": "⚠️ Message blocked by security guardrail."}) + "\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(blocked(), media_type="text/event-stream")

    # Route query
    route = await asyncio.get_event_loop().run_in_executor(None, lambda: route_query(clean_q))

    if route == "DIRECT_CHAT":
        prompt = clean_q
        model = FAST_MODEL
    else:
        # Retrieve context
        docs = await retrieve_async(clean_q, source_filter)
        valid_docs = []
        for doc in docs[:5]:
            relevant = await asyncio.get_event_loop().run_in_executor(
                None, lambda d=doc: check_relevance(clean_q, d)
            )
            if relevant:
                valid_docs.append(doc)

        if not valid_docs:
            async def no_context():
                yield "data: " + json.dumps({"token": "I couldn't find relevant information in my knowledge base for this query."}) + "\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(no_context(), media_type="text/event-stream")

        context = "\n\n".join(valid_docs)
        model = SLOW_MODEL if len(clean_q) > 80 else FAST_MODEL
        prompt = f"""Use the following context to answer the question concisely.

Context:
{context}

Question:
{clean_q}"""

    return StreamingResponse(
        _stream_from_groq(prompt, model),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
