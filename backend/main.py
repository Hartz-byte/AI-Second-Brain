from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from backend.orchestrator.orchestrator import handle_query
from backend.retriever import add_documents
from backend.api.streaming import router as streaming_router
from ingestion.pdf_parser import parse_pdf
from ingestion.youtube_parser import get_transcript
from ingestion.web_scraper import scrape_article
from ingestion.image_parser import analyze_image
from ingestion.audio_parser import transcribe_audio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Second Brain API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register streaming router (provides /ask_stream SSE endpoint)
app.include_router(streaming_router)


@app.get("/")
def root():
    return {"status": "AI Second Brain Backend v2.0 is Running!"}


@app.get("/debug")
def debug():
    import os
    from backend.services.cache_service import is_available as redis_ok
    return {
        "GROQ_KEY_PRESENT": os.getenv("GROQ_API_KEY") is not None,
        "PINECONE_KEY_PRESENT": os.getenv("PINECONE_API_KEY") is not None,
        "HF_TOKEN_PRESENT": os.getenv("HF_TOKEN") is not None,
        "API_BASE": os.getenv("OPENAI_API_BASE"),
        "REDIS_CONNECTED": redis_ok(),
    }


def chunk_text(text, source, size=500, overlap=100):
    chunks = []
    for i in range(0, len(text), size - overlap):
        chunk = text[i:i+size]
        chunks.append({"text": chunk, "source": source})
    return chunks


@app.post("/add")
def add_content(data: dict):
    chunks = chunk_text(data["text"], source="Direct Text Input")
    add_documents(chunks)
    return {"status": "added"}


@app.post("/ask")
async def ask(data: dict):
    """
    Main QA endpoint. Delegates entirely to the async orchestrator.
    Returns rich metadata including route, model, cache_hit, latency, eval scores.
    """
    try:
        question = data.get("question", "")
        data_mode = data.get("data_mode", False)
        source_filter = data.get("source_filter", None)
        result = await handle_query(question, data_mode=data_mode, source_filter=source_filter)
        return result
    except Exception as e:
        logger.error(f"/ask error: {e}", exc_info=True)
        return {"error": str(e)}


# PDF UPLOAD
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile):
    contents = await file.read()
    with open("temp.pdf", "wb") as f:
        f.write(contents)
    text = parse_pdf("temp.pdf")
    chunks = chunk_text(text, source=f"PDF - {file.filename}")
    add_documents(chunks)
    return {"status": "pdf ingested"}


# CSV UPLOAD (DATA ANALYST)
@app.post("/upload_csv")
async def upload_csv(file: UploadFile):
    try:
        from backend.data_analyst import save_csv
        contents = await file.read()
        res = save_csv(contents)
        return {"status": "csv uploaded", "details": res}
    except Exception as e:
        return {"error": str(e)}


# IMAGE UPLOAD (VISION + OCR)
@app.post("/upload_image")
async def upload_image(file: UploadFile):
    try:
        image_bytes = await file.read()
        mime_type = "image/jpeg"
        if file.filename.lower().endswith(".png"):
            mime_type = "image/png"
        image_text = analyze_image(image_bytes, mime_type)
        full_text = f"Image Source: {file.filename}\nVision Analysis & Transcribed Text:\n{image_text}"
        chunks = chunk_text(full_text, source=f"Image - {file.filename}")
        add_documents(chunks)
        return {"status": "image ingested", "details": "Vision analysis and OCR completed."}
    except Exception as e:
        return {"error": str(e)}


# AUDIO TRANSCRIPTION (WHISPER)
@app.post("/transcribe_audio")
async def transcribe_audio_endpoint(file: UploadFile):
    try:
        audio_bytes = await file.read()
        text = transcribe_audio(audio_bytes, file.filename)
        return {"transcription": text}
    except Exception as e:
        return {"error": str(e)}


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

    chunks = chunk_text(text, source=f"YouTube Video - {video_id}")
    add_documents(chunks)
    return {"status": "YouTube transcript added"}


# WEB SCRAPER
@app.post("/scrape")
def scrape(data: dict):
    text = scrape_article(data["url"])
    chunks = chunk_text(text, source=f"Web Article - {data['url']}")
    add_documents(chunks)
    return {"status": "article added"}
