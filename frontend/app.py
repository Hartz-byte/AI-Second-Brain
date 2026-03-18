import streamlit as st
import requests
import os
from audio_recorder_streamlit import audio_recorder
import streamlit.components.v1 as components

st.set_page_config(page_title="AI Second Brain", layout="wide")

# Handle Streamlit Secrets (for Cloud) or Environment Variables (for local/Render)
def get_api_url():
    # 1. Try st.secrets (best for Streamlit Cloud)
    try:
        if "API_URL" in st.secrets:
            return st.secrets["API_URL"].strip("/")
    except Exception:
        pass
    
    # 2. Try os.getenv (best for Local or other clouds)
    env_url = os.getenv("API_URL")
    if env_url:
        return env_url.strip("/")
        
    # 3. Fallback to Localhost
    return "http://localhost:8000"

# Sidebar connection indicator
API = get_api_url()
with st.sidebar:
    # st.caption(f"📍 Backend: `{API}`")
    st.info(f"💡 **Note:** The backend gets inactive (Render Free Tier), click [here]({API}) to wake it up.")
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

    # Text-to-Speech Toggle
    mute_tts = st.toggle("🔇 Mute Voice Assistant", value=False)

    st.divider()

    st.subheader("🔍 Knowledge Scope")
    st.caption("Filter which sources the AI searches")
    scope_options = ["All", "PDF", "YouTube", "Image", "Web Article", "Direct Text Input"]
    selected_scope = st.selectbox("Search in:", scope_options, index=0, label_visibility="collapsed")
    source_filter = None if selected_scope == "All" else selected_scope

    st.divider()

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
    st.header("⚙️ Data Ingestion Options")
    
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

    # 2.5 Add Image
    with st.expander("🖼️ Upload Image (Vision & OCR)"):
        img_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
        if st.button("Process Image") and img_file:
            with st.spinner("Analyzing image..."):
                try:
                    target_api = get_api_url()
                    files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
                    r = requests.post(f"{target_api}/upload_image", files=files)
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            st.error(res["error"])
                            add_log(f"Error adding Image: {res['error']}")
                        else:
                            st.success("Image ingested successfully!")
                            add_log(f"Successfully processed Image: {img_file.name}")
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    
    # 2.7 Add CSV for Data Analyst
    with st.expander("📊 Upload CSV (Data Analyst)"):
        csv_file = st.file_uploader("Upload Data", type=["csv"])
        if st.button("Load Data") and csv_file:
            with st.spinner("Analyzing dataset schema..."):
                try:
                    target_api = get_api_url()
                    files = {"file": (csv_file.name, csv_file.getvalue(), "text/csv")}
                    r = requests.post(f"{target_api}/upload_csv", files=files)
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            st.error(res["error"])
                            add_log(f"Error adding CSV: {res['error']}")
                        else:
                            st.success("Dataset loaded!")
                            add_log(f"Ready for Data Analysis: {csv_file.name}")
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
            st.caption("No activity yet.")
        else:
            for log in reversed(st.session_state.logs[-8:]):
                st.caption(f"↳ {log}")


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
            # Permanently re-render eval scores if stored in history
            if message["role"] == "assistant" and message.get("eval"):
                ev = message["eval"]
                rel = ev.get("relevance", 0)
                faith = ev.get("faithfulness", 0)
                overall = ev.get("overall", 0)
                score_color = "🟢" if overall >= 0.6 else ("🟡" if overall >= 0.3 else "🔴")
                st.caption(f"{score_color} **Quality** — Relevance: `{rel:.2f}` | Faithfulness: `{faith:.2f}` | Overall: `{overall:.2f}`")
            if message.get("guardrail_warning"):
                st.warning("⚠️ Response flagged by guardrail — treat with care.", icon="🛡️")

    # React to user input (Text or Voice)
    prompt = st.chat_input("Ask something about your knowledge base...")
    
    # Audio recorder - JS hack to dynamically lock it strictly inside the chat input box and style it
    float_js = """
    <script>
    const updatePosition = () => {
        const iframes = window.parent.document.querySelectorAll('iframe[title="audio_recorder_streamlit.audio_recorder"]');
        const chatInput = window.parent.document.querySelector('[data-testid="stChatInput"]');
        if (iframes.length > 0 && chatInput) {
            const micIframe = iframes[0];
            const rect = chatInput.getBoundingClientRect();
            micIframe.style.position = 'fixed';
            micIframe.style.zIndex = '999999';
            micIframe.style.width = '35px';
            micIframe.style.height = '35px';
            micIframe.style.backgroundColor = 'transparent';
            micIframe.style.border = 'none';
            micIframe.style.pointerEvents = 'auto';
            // Adjusted position: closer to send button, perfectly centered vertically
            micIframe.style.left = (rect.right - 90) + 'px'; 
            micIframe.style.top = (rect.top + (rect.height - 35) / 2) + 'px';
            
            // Inject deep styles to fix transparency and icon size
            try {
                const micDoc = micIframe.contentDocument || micIframe.contentWindow.document;
                if (micDoc) {
                    let styleTag = micDoc.getElementById('cortex-mic-fix');
                    if (!styleTag) {
                        styleTag = micDoc.createElement('style');
                        styleTag.id = 'cortex-mic-fix';
                        micDoc.head.appendChild(styleTag);
                    }
                    styleTag.textContent = `
                        body, html { background: transparent !important; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; width: 100%; height: 100%; overflow: hidden; }
                        button { background: transparent !important; box-shadow: none !important; border: none !important; padding: 0 !important; cursor: pointer !important; width: 35px !important; height: 35px !important; }
                        svg { width: 26px !important; height: 26px !important; fill: #fca311 !important; transition: transform 0.2s ease; filter: drop-shadow(0px 0px 2px rgba(0,0,0,0.5)); }
                        button:hover svg { transform: scale(1.1); fill: #ffb703 !important; }
                    `;
                }
            } catch(e) {}
        }
    };
    setInterval(updatePosition, 100);
    </script>
    """
    components.html(float_js, height=0, width=0)
    audio_bytes = audio_recorder(
        text="", 
        neutral_color="#fca311", 
        recording_color="#ff0000", 
        key="voice_recorder"
    )
    
    # Prevent the same audio clip from being re-transcribed on every UI refresh (e.g., when a user uploads a file/types a new query)
    if "processed_audio" not in st.session_state:
        st.session_state.processed_audio = set()
        
    if audio_bytes:
        audio_hash = hash(audio_bytes)
        if audio_hash not in st.session_state.processed_audio:
            st.session_state.processed_audio.add(audio_hash)
            with st.spinner("Transcribing audio..."):
                try:
                    target_api = get_api_url()
                    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
                    r = requests.post(f"{target_api}/transcribe_audio", files=files)
                    if r.status_code == 200:
                        res = r.json()
                        if "transcription" in res:
                            prompt = res["transcription"]
                            add_log(f"🎙️ Voice Input Transcribed: '{prompt}'")
                        else:
                            st.error("Error transcribing audio.")
                    else:
                        st.error(f"Backend error transcribing audio: {r.status_code}")
                        st.session_state.processed_audio.remove(audio_hash) # Allow retry on failure
                except Exception as e:
                    st.error(f"Request failed: {e}")
                    st.session_state.processed_audio.remove(audio_hash) # Allow retry on failure

    if prompt:
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    target_api = get_api_url()
                    payload = {
                        "question": prompt,
                        "source_filter": source_filter,
                    }
                    r = requests.post(f"{target_api}/ask", json=payload)
                    if r.status_code == 200:
                        res = r.json()
                        if "error" in res:
                            response_msg = f"**Error:** {res['error']}"
                            st.error(res["error"])
                        else:
                            response_msg = res["answer"]

                            # Guardrail warning banner
                            meta = res.get("metadata", {})
                            guardrail_warning = meta.get("guardrail_warning", False)
                            if guardrail_warning:
                                st.warning("⚠️ **Guardrail Notice:** This response may contain unverified claims — treat with care.", icon="🛡️")

                            st.markdown(response_msg)

                            # Evaluation score badges — always shown
                            eval_scores = meta.get("eval", {})
                            rel = eval_scores.get("relevance", 0)
                            faith = eval_scores.get("faithfulness", 0)
                            overall = eval_scores.get("overall", 0)
                            score_color = "🟢" if overall >= 0.6 else ("🟡" if overall >= 0.3 else "🔴")
                            st.caption(
                                f"{score_color} **Quality** — "
                                f"Relevance: `{rel:.2f}` | "
                                f"Faithfulness: `{faith:.2f}` | "
                                f"Overall: `{overall:.2f}`"
                            )

                            # Metadata activity log
                            if meta:
                                route = meta.get("route", "?")
                                model = meta.get("model_used", "?")
                                latency = meta.get("latency_ms", "?")
                                cache_hit = meta.get("cache_hit", False)
                                self_rag = meta.get("self_rag", "")
                                cache_str = " ⚡ Cache HIT" if cache_hit else ""
                                log_line = f"🤖 Route: **{route}** | Model: `{model}` | ⏱ {latency}ms{cache_str}"
                                if self_rag and self_rag != "N/A":
                                    log_line += f" | 🔍 {self_rag}"
                                add_log(log_line)

                            # Text to Speech auto-play
                            if not mute_tts:
                                escaped_text = response_msg.replace('"', '\\"').replace('\n', ' ')
                                tts_js = f"""
                                <script>
                                    const utterance = new SpeechSynthesisUtterance("{escaped_text}");
                                    window.speechSynthesis.speak(utterance);
                                </script>
                                """
                                components.html(tts_js, height=0)

                        # Store message with eval + guardrail in history for permanent display
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response_msg,
                            "eval": eval_scores if eval_scores else {},
                            "guardrail_warning": guardrail_warning,
                        })
                    else:
                        st.error(f"Backend error: {r.status_code}")
                        st.code(r.text[:500])
                        st.session_state.messages.append({"role": "assistant", "content": "Error: Failed to get response from backend."})
                except Exception as e:
                    error_msg = str(e)
                    if "localhost" in error_msg:
                        st.error("⚠️ **Connection Failed.** Please ensure the backend is running and `API_URL` is configured correctly.")
                    else:
                        st.error(f"Connection failed: {e}")

elif nav_selection == "About the project":
    st.subheader("About the Project")
    st.markdown("""
**AI Second Brain** is a production-grade, Multimodal Agentic RAG (Retrieval-Augmented Generation) system. It acts as your personal AI knowledge assistant — letting you ingest any content, then query it using text or voice, with answers grounded in your own data.

---

### ✨ Core Features

| Feature | Description |
|---|---|
| 📄 PDF Ingestion | Extract & index full-text from PDF documents |
| 🌐 Web Scraping | Ingest any article or web page by URL |
| 🎥 YouTube Transcripts | Auto-fetch & index video transcripts |
| 🖼️ Vision & OCR | Upload images — AI describes & transcribes visual content |
| 📊 AI Data Analyst | Upload CSVs, ask natural language questions about your data |
| 📝 Direct Text | Paste raw notes or snippets directly |
| 🎙️ Voice Input | Speak your question via Whisper STT |
| 🔊 Voice Output | Hear AI responses via Web Speech API TTS |
| 🔍 Knowledge Scope | Filter searches by source type (PDF, YouTube, Image, etc.) |
| ⚡ Redis Caching | Instant answers for repeated queries |
| 🛡️ Input Guardrails | Detects & blocks prompt injection attacks |
| 📐 Output Guardrails | Faithfulness grounding check — flags potential hallucinations |
| 📊 Quality Scores | Auto-scores every response on Relevance & Faithfulness |
| 🔁 Retry / Fallback | Auto-retries failed API calls; falls back to alternate model |
| 🌊 Streaming | Real-time token streaming via /ask_stream SSE endpoint |

---

### 🤖 Agentic AI Architecture

```
User Query → Cache Check → Input Guardrail → Agent Router
       ├── VECTOR_SEARCH → Pinecone + Self-RAG Filter → LLM
       ├── DATA_ANALYST  → Pandas Schema + LLM Analysis
       └── DIRECT_CHAT   → Direct LLM Response
                              ↓
             Output Guardrail → Evaluation Score → Cache Write
```

**Key AI Techniques:**
- **Hybrid Retrieval**: Dense (vector) + Sparse (BM25 keyword) retrieval combined
- **Self-RAG (Reflection)**: Retrieved chunks are individually graded for relevance before answering — eliminates hallucinations
- **Dynamic LLM Routing**: Simple queries → fast model; complex queries → powerful model (cost optimized)
- **Multi-Agent Orchestration**: Intent classifier routes to the best specialized tool
- **Async Parallel Processing**: Relevance checks run in parallel via `asyncio.gather`

---

### 🛠️ Tech Stack & Tools

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit, `audio_recorder_streamlit`, Web Speech API |
| **Backend API** | FastAPI (Python 3.11), async endpoints |
| **Orchestrator** | Custom async pipeline (`orchestrator.py`) |
| **Vector Database** | Pinecone Serverless (AWS us-east-1) |
| **Caching** | Redis Cloud (30MB free tier) |
| **Embeddings** | `all-MiniLM-L6-v2` — Hugging Face Inference API |
| **LLM Engine** | Groq API (ultra-fast LPU inference) |
| **Deployment** | Render (backend) + Streamlit Cloud (frontend) |

---

### 🧠 AI Models Used

| Model | Purpose |
|---|---|
| `llama-3.3-70b-versatile` | Core reasoning & complex answer generation |
| `llama-3.1-8b-instant` | Fast routing, Self-RAG grading, simple queries |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Vision analysis & OCR (image understanding) |
| `whisper-large-v3` | Speech-to-Text transcription |
| `all-MiniLM-L6-v2` | Semantic document embedding (384-dim vectors) |

---

### ⭐️ Liked my work?
Check out the [GitHub repo](https://github.com/Hartz-byte/AI-Second-Brain) and give it a star!
    """)

