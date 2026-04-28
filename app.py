import os
import uuid
import json
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Assistant",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background-color: #0a0a0f;
    color: #e2e2e8;
    font-family: 'IBM Plex Sans', sans-serif;
}

[data-testid="stAppViewContainer"] {
    background: #0a0a0f;
    background-image:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99, 102, 241, 0.12), transparent),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(139, 92, 246, 0.06), transparent);
}

[data-testid="stHeader"] { background: transparent !important; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(10, 10, 18, 0.95) !important;
    border-right: 1px solid rgba(99, 102, 241, 0.12) !important;
    backdrop-filter: blur(12px);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

.sidebar-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #52525b;
    margin: 1.5rem 0 0.75rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

.source-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.7rem;
    margin: 0.2rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-family: 'IBM Plex Mono', monospace;
    border: 1px solid rgba(99, 102, 241, 0.25);
    background: rgba(99, 102, 241, 0.08);
    color: #a5b4fc;
}
.source-chip .chip-icon { font-size: 0.7rem; }

/* ── Main area ── */
.block-container {
    max-width: 960px !important;
    padding: 2rem 2rem 6rem !important;
    margin: 0 auto;
}

.hero-compact {
    text-align: center;
    padding: 1.5rem 0 1rem;
}
.hero-compact h1 {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.6rem;
    font-weight: 600;
    color: #f0f0f6;
    margin: 0;
    letter-spacing: -0.02em;
}
.hero-compact h1 span { color: #818cf8; }
.hero-compact p {
    font-size: 0.82rem;
    color: #52525b;
    margin: 0.4rem 0 0;
    font-family: 'IBM Plex Mono', monospace;
}

/* ── Status bar ── */
.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    margin-bottom: 1rem;
}
.status-bar.ready {
    background: rgba(34, 197, 94, 0.08);
    border: 1px solid rgba(34, 197, 94, 0.2);
    color: #86efac;
}
.status-bar.waiting {
    background: rgba(99, 102, 241, 0.06);
    border: 1px solid rgba(99, 102, 241, 0.15);
    color: #818cf8;
}
.status-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.status-dot.green { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-dot.blue  { background: #6366f1; }

/* ── Ingest panel ── */
.ingest-panel {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
}
.ingest-panel:hover { border-color: rgba(99, 102, 241, 0.2); }

.step-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.65rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #52525b;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.step-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(99,102,241,0.2), transparent);
}
.step-num {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #818cf8;
    font-size: 0.55rem;
    font-weight: 600;
    flex-shrink: 0;
}

/* ── Source citation cards ── */
.source-card {
    background: rgba(99, 102, 241, 0.04);
    border: 1px solid rgba(99, 102, 241, 0.12);
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.4rem 0;
    font-size: 0.8rem;
    color: #a1a1aa;
    line-height: 1.5;
}
.source-card-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #818cf8;
    margin-bottom: 0.4rem;
    font-weight: 500;
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    border-radius: 6px !important;
    border: 1px solid rgba(99, 102, 241, 0.4) !important;
    background: rgba(99, 102, 241, 0.1) !important;
    color: #a5b4fc !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: rgba(99, 102, 241, 0.22) !important;
    border-color: rgba(99, 102, 241, 0.7) !important;
    color: #e0e7ff !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
    color: #e2e2e8 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.9rem !important;
    caret-color: #6366f1 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(99, 102, 241, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.08) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: #3f3f46 !important; }
.stTextInput label, .stTextArea label, .stFileUploader label, .stSelectbox label, .stSlider label {
    color: #71717a !important;
    font-size: 0.78rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(99, 102, 241, 0.25) !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(99, 102, 241, 0.5) !important; }

/* ── Alerts ── */
.stSuccess > div {
    background: rgba(34, 197, 94, 0.08) !important;
    border: 1px solid rgba(34, 197, 94, 0.2) !important;
    border-radius: 6px !important; color: #86efac !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
}
.stWarning > div {
    background: rgba(234, 179, 8, 0.08) !important;
    border: 1px solid rgba(234, 179, 8, 0.2) !important;
    border-radius: 6px !important; color: #fde68a !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
}
.stError > div {
    background: rgba(239, 68, 68, 0.08) !important;
    border: 1px solid rgba(239, 68, 68, 0.2) !important;
    border-radius: 6px !important; color: #fca5a5 !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
}
.stInfo > div {
    background: rgba(99, 102, 241, 0.06) !important;
    border: 1px solid rgba(99, 102, 241, 0.18) !important;
    border-radius: 6px !important; color: #a5b4fc !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.78rem !important;
}

/* ── Radio as pills ── */
.stRadio > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 0.4rem !important;
    flex-wrap: wrap !important;
}
.stRadio > div > label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 6px !important;
    padding: 0.45rem 1rem !important;
    cursor: pointer !important;
    color: #71717a !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.75rem !important;
    transition: all 0.15s !important;
}
.stRadio > div > label:hover {
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #a5b4fc !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
    padding: 1rem 1.2rem !important;
    font-size: 0.92rem !important;
}
[data-testid="stChatInput"] > div {
    border-color: rgba(99, 102, 241, 0.3) !important;
    background: rgba(255,255,255,0.03) !important;
}
[data-testid="stChatInput"] textarea {
    color: #e2e2e8 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.76rem !important;
    color: #818cf8 !important;
    background: rgba(99, 102, 241, 0.04) !important;
    border-radius: 6px !important;
}

/* ── Select box ── */
.stSelectbox > div > div {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #e2e2e8 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3f3f46; }

/* ── Divider ── */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 1.2rem 0;
}
</style>
""", unsafe_allow_html=True)


# ── Session state ───────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "indexed" not in st.session_state:
    st.session_state["indexed"] = False
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "ingested_sources" not in st.session_state:
    st.session_state["ingested_sources"] = []
if "model" not in st.session_state:
    st.session_state["model"] = "llama3-8b-8192"
if "temperature" not in st.session_state:
    st.session_state["temperature"] = 0.2

session_id = st.session_state["session_id"]

AVAILABLE_MODELS = [
    "llama3-8b-8192",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
]


# ── API Helpers ─────────────────────────────────────────────────────────────────

def api_ingest(input_type, input_data):
    try:
        if input_type == "pdf":
            resp = requests.post(
                f"{API_BASE}/ingest/pdf",
                files={"file": (input_data.name, input_data.getvalue(), "application/pdf")},
                params={"session_id": session_id},
                timeout=60,
            )
        elif input_type == "link":
            resp = requests.post(
                f"{API_BASE}/ingest/link",
                json={"url": input_data, "session_id": session_id},
                timeout=60,
            )
        else:
            resp = requests.post(
                f"{API_BASE}/ingest/text",
                json={"content": input_data, "session_id": session_id},
                timeout=60,
            )
        if resp.status_code == 200:
            return True, resp.json()
        return False, resp.json().get("detail", resp.text)
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to backend at {API_BASE}. Is the API running?"
    except requests.exceptions.Timeout:
        return False, "Request timed out. The document may be too large."


def api_query_stream(question):
    """Generator that yields tokens and returns sources via session state."""
    try:
        resp = requests.post(
            f"{API_BASE}/query/stream",
            json={"question": question, "session_id": session_id},
            stream=True,
            timeout=120,
        )
        if resp.status_code != 200:
            detail = resp.json().get("detail", resp.text)
            st.error(f"✗ {detail}")
            return

        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event["type"] == "sources":
                st.session_state["_pending_sources"] = event["data"]
            elif event["type"] == "token":
                yield event["data"]
            elif event["type"] == "done":
                break
    except requests.exceptions.ConnectionError:
        st.error(f"Cannot connect to backend at {API_BASE}.")
    except requests.exceptions.Timeout:
        st.error("Response timed out.")


def api_update_config():
    try:
        requests.post(
            f"{API_BASE}/session/{session_id}/config",
            json={
                "session_id": session_id,
                "model": st.session_state["model"],
                "temperature": st.session_state["temperature"],
            },
            timeout=10,
        )
    except Exception:
        pass


def api_export():
    try:
        resp = requests.get(f"{API_BASE}/session/{session_id}/export", timeout=10)
        if resp.status_code == 200:
            return resp.text
    except Exception:
        pass
    return None


# ── Sidebar ─────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 0.5rem;">
        <span style="font-family: 'IBM Plex Mono', monospace; font-size: 1.1rem; font-weight: 600; color: #f0f0f6;">
            ⬡ RAG<span style="color: #818cf8;">.</span>assistant
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-title">Model Configuration</div>', unsafe_allow_html=True)

    new_model = st.selectbox(
        "LLM Model",
        AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(st.session_state["model"]) if st.session_state["model"] in AVAILABLE_MODELS else 0,
        key="model_select",
    )
    if new_model != st.session_state["model"]:
        st.session_state["model"] = new_model
        api_update_config()

    new_temp = st.slider("Temperature", 0.0, 1.0, st.session_state["temperature"], 0.05, key="temp_slider")
    if new_temp != st.session_state["temperature"]:
        st.session_state["temperature"] = new_temp
        api_update_config()

    # ── Knowledge Base ──
    st.markdown('<div class="sidebar-title">Knowledge Base</div>', unsafe_allow_html=True)

    if st.session_state["ingested_sources"]:
        chips_html = ""
        for src in st.session_state["ingested_sources"]:
            icon = {"pdf": "📄", "link": "🔗", "text": "✍️"}.get(src["type"], "📎")
            name = src["name"][:30] + "…" if len(src["name"]) > 30 else src["name"]
            chips_html += f'<span class="source-chip"><span class="chip-icon">{icon}</span>{name}</span>'
        st.markdown(chips_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<span style="font-size: 0.78rem; color: #3f3f46; font-family: IBM Plex Mono, monospace;">No sources indexed yet</span>',
            unsafe_allow_html=True,
        )

    # ── Actions ──
    st.markdown('<div class="sidebar-title">Actions</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑 New Session", use_container_width=True):
            try:
                requests.delete(f"{API_BASE}/session/{session_id}", timeout=5)
            except Exception:
                pass
            st.session_state["session_id"] = str(uuid.uuid4())
            st.session_state["indexed"] = False
            st.session_state["chat_history"] = []
            st.session_state["ingested_sources"] = []
            st.rerun()
    with col2:
        if st.button("📥 Export", use_container_width=True):
            md = api_export()
            if md:
                st.download_button("⬇ Download", md, f"chat_{session_id[:8]}.md", "text/markdown", use_container_width=True)
            else:
                st.info("No history to export.")

    st.markdown(
        f'<div style="margin-top:2rem; font-size:0.6rem; color:#27272a; font-family:IBM Plex Mono,monospace;">Session {session_id[:8].upper()}</div>',
        unsafe_allow_html=True,
    )


# ── Main Area ───────────────────────────────────────────────────────────────────

# Hero
st.markdown("""
<div class="hero-compact">
    <h1>RAG<span>.</span>assistant</h1>
    <p>Index documents · Ask questions · Get grounded answers</p>
</div>
""", unsafe_allow_html=True)

# Status bar
if st.session_state["indexed"]:
    n = len(st.session_state["ingested_sources"])
    st.markdown(f"""
    <div class="status-bar ready">
        <div class="status-dot green"></div>
        <span>Knowledge base active &mdash; {n} source{'s' if n != 1 else ''} indexed</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="status-bar waiting">
        <div class="status-dot blue"></div>
        <span>Awaiting data &mdash; index a document to begin</span>
    </div>
    """, unsafe_allow_html=True)

# ── Ingest Section ──────────────────────────────────────────────────────────────

with st.expander("⬡  Add to Knowledge Base" if st.session_state["indexed"] else "⬡  Index Your First Document", expanded=not st.session_state["indexed"]):
    st.markdown('<div class="step-label"><span class="step-num">1</span> Choose source type</div>', unsafe_allow_html=True)

    source_map = {"📄  PDF": "pdf", "🔗  URL": "link", "✍️  Text": "text"}
    selected_label = st.radio(
        "source",
        list(source_map.keys()),
        horizontal=True,
        label_visibility="collapsed",
    )
    input_type = source_map[selected_label]

    st.markdown('<div class="step-label"><span class="step-num">2</span> Provide content</div>', unsafe_allow_html=True)

    input_data = None
    if input_type == "pdf":
        input_data = st.file_uploader("Drop a PDF here", type=["pdf"], key="pdf_upload")
    elif input_type == "link":
        input_data = st.text_input("Website URL", placeholder="https://example.com/article", key="url_input")
    else:
        input_data = st.text_area("Paste your content", height=150, placeholder="Enter text to index...", key="text_input")

    if st.button("⬡  Index Content", use_container_width=True, key="ingest_btn"):
        if not input_data:
            st.warning("Provide content before indexing.")
        else:
            with st.spinner("Embedding and indexing..."):
                ok, result = api_ingest(input_type, input_data)
            if ok:
                st.session_state["indexed"] = True
                source_name = ""
                if input_type == "pdf":
                    source_name = input_data.name
                elif input_type == "link":
                    source_name = input_data
                else:
                    source_name = f"Text ({len(input_data)} chars)"
                st.session_state["ingested_sources"].append({"name": source_name, "type": input_type})
                st.success(f"✓ {result.get('message', 'Indexed successfully.')}")
                st.rerun()
            else:
                st.error(f"✗ {result}")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Chat Interface ──────────────────────────────────────────────────────────────

if not st.session_state["indexed"]:
    st.info("Index a document above to start asking questions.")
else:
    # Display chat history
    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "⬡"):
            st.markdown(msg["content"])
            if msg.get("sources"):
                with st.expander(f"📎 {len(msg['sources'])} source chunks referenced"):
                    for i, src in enumerate(msg["sources"], 1):
                        src_name = src.get("source_name", "Unknown")
                        page = src.get("page")
                        header = f"Source {i}: {src_name}"
                        if page:
                            header += f" (p. {page})"
                        st.markdown(f"""
                        <div class="source-card">
                            <div class="source-card-header">{header}</div>
                            {src['content']}
                        </div>
                        """, unsafe_allow_html=True)

    # Chat input
    if prompt := st.chat_input("Ask anything about your documents..."):
        # Show user message
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="🧑"):
            st.markdown(prompt)

        # Stream assistant response
        with st.chat_message("assistant", avatar="⬡"):
            st.session_state["_pending_sources"] = []
            response = st.write_stream(api_query_stream(prompt))

            if response:
                sources = st.session_state.get("_pending_sources", [])
                st.session_state["chat_history"].append({
                    "role": "assistant",
                    "content": response,
                    "sources": sources,
                })

                if sources:
                    with st.expander(f"📎 {len(sources)} source chunks referenced"):
                        for i, src in enumerate(sources, 1):
                            src_name = src.get("source_name", "Unknown")
                            page = src.get("page")
                            header = f"Source {i}: {src_name}"
                            if page:
                                header += f" (p. {page})"
                            st.markdown(f"""
                            <div class="source-card">
                                <div class="source-card-header">{header}</div>
                                {src['content']}
                            </div>
                            """, unsafe_allow_html=True)