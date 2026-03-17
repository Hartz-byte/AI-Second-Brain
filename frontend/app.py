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
                            
                            # Add Metadata Logging
                            meta = res.get("metadata", {})
                            if meta:
                                route = meta.get("route", "Unknown")
                                log_str = f"🤖 Agent Routed to: **{route}**"
                                if "self_rag" in meta:
                                    log_str += f" | 🔍 Self-RAG: *{meta['self_rag']}*"
                                add_log(log_str)
                            
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
    **AI Second Brain** is a highly capable Multimodal Agentic Retrieval-Augmented Generation (RAG) application. It acts as your ultimate, personal knowledge assistant.

    It allows you to build a custom knowledge base by combining various data sources (text, video, and images), and then uses an intelligent agent router to determine how to best answer your queries.

    ### ✨ Key Features
    - **Multimodal Ingestion**: 
        - **PDFs & Web Scraping**: Ingest lengthy documents and website content seamlessly.
        - **YouTube Transcripts**: Extract knowledge directly from video content.
        - **Vision & OCR**: Upload images and let the Llama 3.2 Vision model transcribe text and comprehensively describe visual content.
        - **Tabular Data Analyst**: Upload CSVs to instantly talk to an intelligent Data Analyst that uses Pandas to summarize schemas and generate insights.
    - **Agentic Routing System**: The backend utilizes a dynamic LLM router that actively interprets your intent and directs queries to the appropriate tools (Vector Search vs Data Analyst vs Direct Chat).
    - **Self-Improving RAG (Reflection)**: Eradicates hallucinations! Retrieves documents and autonomously grades them for strict relevance before attempting to draft a response. 
    - **Real-Time Voice Assistant**: Use the floating microphone to submit queries via Speech-to-Text (powered by Whisper API), and listen to answers out loud with automatic Text-to-Speech!
    - **Persistent Cloud Vector Storage**: Pinecone Serverless guarantees you never lose context between sessions.
    
    ### 🛠️ Tech Stack & Tools
    - **Frontend Ecosystem**: Streamlit, `audio_recorder_streamlit`, Web Speech API (JavaScript)
    - **Backend Framework**: FastAPI (Python), Pandas SDK
    - **Cloud Vector Database**: Pinecone Serverless
    - **Embeddings**: `all-MiniLM-L6-v2` via Hugging Face Inference API
    - **Generative AI Engines**: Groq API
        - *Llama 3.3 70B* (Core Reasoning & Generation)
        - *Llama 4 Scout 17B* (Vision & Image Understanding)
        - *Llama 3.1 8B* (Ultra-fast Self-RAG relevance checker)
        - *Whisper Large V3* (Flawless Speech-to-Text)
    
    ---
    ### ⭐️ Support the Project
    **Liked my work?** Check out the [GitHub repo](https://github.com/Hartz-byte/AI-Second-Brain) and give it a star!
    """)
