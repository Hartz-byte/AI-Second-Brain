from backend.llm_client import client, MODEL_NAME

def route_query(question: str) -> str:
    """
    Decides the best tool to use based on the user's question.
    Returns one of: 'VECTOR_SEARCH', 'DATA_ANALYST', 'DIRECT_CHAT'
    """
    prompt = f"""
You are an intelligent router for an AI assistant.
Evaluate the user's question and decide which tool should handle it.

Available Tools:
1. "VECTOR_SEARCH": Use this for questions that likely require searching the user's personal knowledge base (documents, PDFs, youtube videos, articles, images). 
2. "DATA_ANALYST": Use this ONLY if the user specifically asks to analyze data from an uploaded CSV/Excel file, or asks for statistics, charts, or pandas operations.
3. "DIRECT_CHAT": Use this for general greetings, casual conversation, or basic world knowledge that doesn't require specific personal context.

Reply with EXACTLY ONE word matching the tool names above. No other text.

Question: {question}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=10
        )
        decision = response.choices[0].message.content.strip().upper()
        if decision not in ["VECTOR_SEARCH", "DATA_ANALYST", "DIRECT_CHAT"]:
            return "VECTOR_SEARCH" # Fallback
        return decision
    except Exception:
        return "VECTOR_SEARCH"

def check_relevance(question: str, context_chunk: str) -> bool:
    """
    Self-RAG Step: Checks if a retrieved chunk is actually relevant to the question.
    """
    prompt = f"""
You are a strict grading assistant. 
Determine if the provided context contains any useful information to help answer the user's question.
Reply exactly with "YES" or "NO".

Question: {question}

Context:
{context_chunk}
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant", # Use a smaller, faster model for simple YES/NO evaluation
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=5
        )
        decision = response.choices[0].message.content.strip().upper()
        return "YES" in decision
    except Exception:
        return True # Fallback to using it if API fails
