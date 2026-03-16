from backend.embeddings import embed_texts
from vector_store.pinecone_db import VectorStore

vector_db = VectorStore()

def add_documents(metadata_chunks):
    # metadata_chunks is a list of {"text": "...", "source": "..."}
    texts = [doc["text"] for doc in metadata_chunks]
    embeddings = embed_texts(texts)
    
    vector_db.add(embeddings, metadata_chunks)

def retrieve(query):
    query_embedding = embed_texts([query])
    
    # We now pass the raw query string + the vector embedding!
    docs = vector_db.search(query, query_embedding)

    if not docs:
        return ["No knowledge found in the database."]

    # docs is a list of metadata dicts, convert back to contextual strings
    formatted_docs = []
    for doc in docs:
        source_tag = f"Source: {doc['source']}"
        formatted_docs.append(f"{source_tag}\n{doc['text']}")

    return formatted_docs
