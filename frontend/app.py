import streamlit as st
import requests
import os

st.set_page_config(page_title="AI Second Brain", layout="wide")

# Handle Streamlit Secrets (for Cloud) or Environment Variables (for local/Render)
def get_api_url():
    # 1. Try st.secrets (best for Streamlit Cloud)
    if "API_URL" in st.secrets:
        return st.secrets["API_URL"].strip("/")
    
    # 2. Try os.getenv (best for Local or other clouds)
    env_url = os.getenv("API_URL")
    if env_url:
        return env_url.strip("/")
        
    # 3. Fallback to Localhost
    return "http://localhost:8000"

# Sidebar connection indicator
API = get_api_url()
with st.sidebar:
    st.caption(f"📍 Backend: `{API}`")
    if st.button("Check Connection"):
        try:
            r = requests.get(f"{API}/")
            if r.status_code == 200:
                st.success("✅ Backend Online!")
            else:
                st.error(f"❌ Backend offline ({r.status_code})")
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
    
    if st.button("🔄 Clear Chat & Logs"):
        st.session_state.messages = []
        st.session_state.logs = []
        st.rerun()

# Initialize session state for messages and logs
if "messages" not in st.session_state:
    st.session_state.messages = []

if "logs" not in st.session_state:
    st.session_state.logs = []

def add_log(msg):
    st.session_state.logs.append(msg)

st.title("AI Second Brain 🧠")

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Data Ingestion")
    
    # 1. Add Text
    with st.expander("📝 Add Text content"):
        content = st.text_area("Paste knowledge")
        if st.button("Add Text"):
            with st.spinner("Adding..."):
                try:
                    # Get fresh URL every time
                    target_api = get_api_url()
                    r = requests.post(f"{target_api}/add", json={"text": content})
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            st.error(res["error"])
                            add_log(f"Error adding text: {res['error']}")
                        else:
                            st.success("Content added")
                            add_log("Successfully added text content.")
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                        add_log(f"Backend error {r.status_code}")
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    add_log(f"Request failed: {e}")

    # 2. Add PDF
    with st.expander("📄 Upload PDF"):
        pdf_file = st.file_uploader("Upload PDF", type=["pdf"])
        if st.button("Process PDF") and pdf_file:
            with st.spinner("Processing PDF..."):
                try:
                    target_api = get_api_url()
                    files = {"file": (pdf_file.name, pdf_file.getvalue(), "application/pdf")}
                    r = requests.post(f"{target_api}/upload_pdf", files=files)
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            st.error(res["error"])
                            add_log(f"Error adding PDF: {res['error']}")
                        else:
                            st.success("PDF ingested")
                            add_log(f"Successfully processed PDF: {pdf_file.name}")
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # 3. Add YouTube
    with st.expander("🎥 Add YouTube Video"):
        youtube_url = st.text_input("YouTube URL")
        if st.button("Process YouTube"):
            with st.spinner("Fetching transcript..."):
                try:
                    target_api = get_api_url()
                    r = requests.post(f"{target_api}/youtube", json={"url": youtube_url})
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            st.error(res["error"])
                            add_log(f"Error adding YouTube video: {res['error']}")
                        else:
                            st.success("YouTube transcript added")
                            add_log(f"Successfully added YouTube transcript for {youtube_url}")
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                except Exception as e:
                    st.error(f"Request failed: {e}")

    # 4. Add Web Article
    with st.expander("🌐 Add Web Article"):
        url = st.text_input("Article URL")
        if st.button("Scrape Article"):
            with st.spinner("Scraping..."):
                try:
                    target_api = get_api_url()
                    r = requests.post(f"{target_api}/scrape", json={"url": url})
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            st.error(res["error"])
                            add_log(f"Error scraping article: {res['error']}")
                        else:
                            st.success("Article added")
                            add_log(f"Successfully scraped article: {url}")
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    
    st.divider()
    st.header("📜 Activity Logs")
    v_logs = st.container()
    with v_logs:
        if not st.session_state.logs:
            st.write("No activity yet.")
        else:
            for log in reversed(st.session_state.logs):
                st.write(f"- {log}")


# NAVIGATION BAR
nav_selection = st.radio(
    "Navigation", 
    ["Chat with your Second Brain", "About the project"], 
    horizontal=True, 
    label_visibility="collapsed"
)

if nav_selection == "Chat with your Second Brain":
    # MAIN CHAT AREA
    st.subheader("Chat with your Second Brain")

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # React to user input
    if prompt := st.chat_input("Ask something about your knowledge base..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get fresh API URL inside the block
                    target_api = get_api_url()
                    r = requests.post(f"{target_api}/ask", json={"question": prompt})
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            response_msg = f"**Error:** {res['error']}"
                            st.error(res["error"])
                        else:
                            response_msg = res["answer"]
                            st.markdown(response_msg)
                            
                        # Add assistant response to chat history
                        st.session_state.messages.append({"role": "assistant", "content": response_msg})
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                        # Keep history consistent
                        st.session_state.messages.append({"role": "assistant", "content": "Error: Failed to get response from backend."})
                except Exception as e:
                    error_msg = str(e)
                    if "localhost" in error_msg:
                        st.error("⚠️ **Connection Failed: The app is still trying to look for the backend on 'localhost'.**\n\nPlease check your Streamlit Cloud **Secrets** and ensure `API_URL` is set to your Render URL.")
                    else:
                        st.error(f"Connection failed: {e}")

elif nav_selection == "About the project":
    st.subheader("About the Project")
    st.markdown("""
    **AI Second Brain** is a powerful Retrieval-Augmented Generation (RAG) application that acts as your personal knowledge assistant.

    It allows you to build a custom knowledge base by combining various data sources, and then ask questions against that aggregated knowledge using an LLM.

    ### ✨ Key Features
    - **Persistent Pinecone Vector Storage:** Everything you add is saved directly to a cloud Pinecone index so you don't lose data on restarts!
    - **Hybrid Search:** We perform Reciprocal Rank Fusion by combining traditional keyword searches with advanced semantic vector embeddings for extreme accuracy.
    - **Overlapping Chunks:** Text is intelligently sliced with context overlaps so sentences don't cut off awkwardly.
    - **Source Tracking:** The bot knows *exactly* where a fact came from (e.g. `PDF - document.pdf`, `YouTube Video - ...`) and feeds that into the prompt.
    - **Beautiful UI:** A full chatbot experience with a live ingestion Activity Log.

    ### 🛠️ Tech Stack & Tools
    - **Frontend:** Streamlit 
    - **Backend:** FastAPI, Python
    - **Database:** Pinecone Serverless Cloud Vector Database
    - **Embeddings:** `all-MiniLM-L6-v2` via SentenceTransformers
    - **LLM Engine:** Groq API leveraging `llama-3.3-70b-versatile`
    - **Hybrid Retrieval:** `rank_bm25` (BM25Okapi)
    """)
