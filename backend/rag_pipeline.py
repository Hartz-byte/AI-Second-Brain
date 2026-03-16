from backend.retriever import retrieve
from backend.llm_client import generate_answer
from backend.agent import route_query, check_relevance

def ask_question(question, data_mode=False):
    # Route query
    route = route_query(question)
    metadata = {"route": route}
    
    if route == "DATA_ANALYST" or data_mode:
        metadata["route"] = "DATA_ANALYST"
        return "DATA_ANALYST_ROUTING_REQUIRED", metadata
        
    if route == "DIRECT_CHAT":
        # Answer directly without searching Pinecone
        return generate_answer("Context is not needed for general conversation. Answer based on your existing knowledge.", question), metadata
    
    # VECTOR_SEARCH Flow (Self-RAG)
    raw_docs = retrieve(question)
    
    if not raw_docs or "No knowledge found" in raw_docs[0]:
        metadata["self_rag"] = "No documents found in knowledge base."
        return "I don't have any specific information in my knowledge base about this.", metadata
        
    valid_docs = []
    # Check top 3 documents for relevance (Self-RAG Step)
    for doc in raw_docs[:3]:
        if check_relevance(question, doc):
            valid_docs.append(doc)
            
    metadata["self_rag"] = f"Relevance check passed for {len(valid_docs)}/3 documents."

    if not valid_docs:
         return "I searched my memory but the results weren't directly relevant to your specific question. Could you modify your query?", metadata
         
    context = "\n".join(valid_docs)
    answer = generate_answer(context, question)

    return answer, metadata
