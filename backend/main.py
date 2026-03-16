from fastapi import FastAPI
from backend.rag_pipeline import ask_question
from backend.retriever import add_documents

app = FastAPI()

@app.get("/")
def home():
    return {"message": "AI Second Brain running"}

@app.post("/add")
def add_content(data: dict):

    text = data["text"]

    chunks = [text[i:i+500] for i in range(0, len(text), 500)]

    add_documents(chunks)

    return {"status": "content added"}

@app.post("/ask")
def ask(data: dict):

    question = data["question"]

    answer = ask_question(question)

    return {"answer": answer}
