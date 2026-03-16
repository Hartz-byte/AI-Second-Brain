from fastapi import FastAPI, UploadFile
from backend.rag_pipeline import ask_question
from backend.retriever import add_documents
from ingestion.pdf_parser import parse_pdf
from ingestion.youtube_parser import get_transcript
from ingestion.web_scraper import scrape_article

app = FastAPI()


def chunk_text(text, size=500):

    return [text[i:i+size] for i in range(0, len(text), size)]


@app.post("/add")
def add_content(data: dict):

    chunks = chunk_text(data["text"])
    add_documents(chunks)

    return {"status": "added"}


@app.post("/ask")
def ask(data: dict):

    answer = ask_question(data["question"])

    return {"answer": answer}


# PDF UPLOAD
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile):

    contents = await file.read()

    with open("temp.pdf", "wb") as f:
        f.write(contents)

    text = parse_pdf("temp.pdf")

    chunks = chunk_text(text)

    add_documents(chunks)

    return {"status": "pdf ingested"}


# YOUTUBE
@app.post("/youtube")
def youtube(data: dict):
    url = data["url"]

    if "v=" in url:
        video_id = url.split("v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
    elif "/shorts/" in url:
        video_id = url.split("/shorts/")[-1].split("?")[0]
    else:
        video_id = url.split("/")[-1].split("?")[0]

    text = get_transcript(video_id)

    if text is None:
        return {"error": "Transcript not available for this video"}

    chunks = chunk_text(text)
    add_documents(chunks)

    return {"status": "YouTube transcript added"}


# WEB SCRAPER
@app.post("/scrape")
def scrape(data: dict):

    text = scrape_article(data["url"])

    chunks = chunk_text(text)

    add_documents(chunks)

    return {"status": "article added"}
