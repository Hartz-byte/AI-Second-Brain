import streamlit as st
import requests

API = "http://localhost:8000"

st.title("AI Second Brain")

# ASK QUESTIONS
st.header("Ask your knowledge base")

question = st.text_input("Ask something")

if st.button("Ask"):

    r = requests.post(
        f"{API}/ask",
        json={"question": question}
    )

    st.write(r.json()["answer"])


# ADD TEXT CONTENT
st.header("Add Text")

content = st.text_area("Paste knowledge")

if st.button("Add Text"):

    r = requests.post(
        f"{API}/add",
        json={"text": content}
    )

    st.success("Content added")


# PDF UPLOAD
st.header("Upload PDF")

pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if st.button("Process PDF") and pdf_file:

    files = {"file": pdf_file.getvalue()}

    r = requests.post(
        f"{API}/upload_pdf",
        files=files
    )

    st.success("PDF ingested")


# YOUTUBE INGESTION
st.header("Add YouTube Video")

youtube_url = st.text_input("YouTube URL")

if st.button("Process YouTube"):

    r = requests.post(
        f"{API}/youtube",
        json={"url": youtube_url}
    )

    st.success("YouTube transcript added")


# WEB ARTICLE
st.header("Add Web Article")

url = st.text_input("Article URL")

if st.button("Scrape Article"):

    r = requests.post(
        f"{API}/scrape",
        json={"url": url}
    )

    st.success("Article added")
