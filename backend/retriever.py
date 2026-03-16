from backend.embeddings import embed_texts
from vector_store.faiss_db import VectorStore

vector_db = VectorStore()

def add_documents(chunks):

    embeddings = embed_texts(chunks)
    vector_db.add(embeddings, chunks)

def retrieve(query):

    query_embedding = embed_texts([query])[0]
    docs = vector_db.search(query_embedding)

    return docs
