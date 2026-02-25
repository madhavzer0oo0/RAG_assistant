import os
import uuid
import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="RAG Assistant",

    layout="wide",
    initial_sidebar_state="collapsed",
)

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

[data-testid="stHeader"] { display: none; }
[data-testid="stSidebar"] { display: none; }
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

.block-container {
    max-width: 900px !important;
    padding: 3rem 2rem 4rem !important;
    margin: 0 auto;
}

.hero {
    text-align: center;
    padding: 3rem 0 2.5rem;
}
.hero-badge {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #6366f1;
    border: 1px solid rgba(99, 102, 241, 0.35);
    padding: 0.35rem 0.9rem;
    border-radius: 2px;
    margin-bottom: 1.5rem;
    background: rgba(99, 102, 241, 0.06);
}
.hero-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 2.6rem;
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #f0f0f6;
    margin: 0 0 0.75rem;
    line-height: 1.1;
}
.hero-title span { color: #818cf8; }
.hero-sub {
    font-size: 1rem;
    color: #71717a;
    font-weight: 300;
    letter-spacing: 0.01em;
}

.step-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    font-weight: 500;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #52525b;
    margin-bottom: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.6rem;
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
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.3);
    color: #818cf8;
    font-size: 0.6rem;
    font-weight: 600;
    flex-shrink: 0;
}

.status-bar {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    padding: 0.6rem 1rem;
    border-radius: 6px;
    margin-bottom: 1.5rem;
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
.status-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.status-dot.green { background: #22c55e; box-shadow: 0 0 6px #22c55e; }
.status-dot.blue  { background: #6366f1; }

.panel {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}
.panel:hover { border-color: rgba(99, 102, 241, 0.2); }

.answer-wrapper {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 8px;
    overflow: hidden;
    margin: 1rem 0;
}
.answer-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1rem;
    background: rgba(99, 102, 241, 0.08);
    border-bottom: 1px solid rgba(99, 102, 241, 0.15);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: #818cf8;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}
.answer-body {
    padding: 1.4rem 1.5rem;
    color: #d4d4e0;
    font-size: 0.975rem;
    line-height: 1.75;
    font-weight: 300;
}

.history-item {
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding: 1.1rem 0;
}
.history-item:last-child { border-bottom: none; }
.history-q {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    color: #a5b4fc;
    margin-bottom: 0.5rem;
    display: flex;
    gap: 0.5rem;
}
.history-q::before { content: '>'; color: #52525b; }
.history-a {
    font-size: 0.9rem;
    color: #a1a1aa;
    line-height: 1.6;
    padding-left: 1rem;
    border-left: 2px solid rgba(99, 102, 241, 0.2);
}

.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.07), transparent);
    margin: 2rem 0;
}

/* Buttons */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    letter-spacing: 0.05em !important;
    border-radius: 6px !important;
    border: 1px solid rgba(99, 102, 241, 0.4) !important;
    background: rgba(99, 102, 241, 0.1) !important;
    color: #a5b4fc !important;
    padding: 0.55rem 1.2rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: rgba(99, 102, 241, 0.22) !important;
    border-color: rgba(99, 102, 241, 0.7) !important;
    color: #e0e7ff !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 6px !important;
    color: #e2e2e8 !important;
    font-family: 'IBM Plex Sans', sans-serif !important;
    font-size: 0.92rem !important;
    caret-color: #6366f1 !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgba(99, 102, 241, 0.6) !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.08) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color: #3f3f46 !important; }
.stTextInput label, .stTextArea label, .stFileUploader label {
    color: #71717a !important;
    font-size: 0.82rem !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px dashed rgba(99, 102, 241, 0.25) !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploader"]:hover { border-color: rgba(99, 102, 241, 0.5) !important; }

/* Alerts */
.stSuccess > div {
    background: rgba(34, 197, 94, 0.08) !important;
    border: 1px solid rgba(34, 197, 94, 0.2) !important;
    border-radius: 6px !important; color: #86efac !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important;
}
.stWarning > div {
    background: rgba(234, 179, 8, 0.08) !important;
    border: 1px solid rgba(234, 179, 8, 0.2) !important;
    border-radius: 6px !important; color: #fde68a !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important;
}
.stError > div {
    background: rgba(239, 68, 68, 0.08) !important;
    border: 1px solid rgba(239, 68, 68, 0.2) !important;
    border-radius: 6px !important; color: #fca5a5 !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important;
}
.stInfo > div {
    background: rgba(99, 102, 241, 0.06) !important;
    border: 1px solid rgba(99, 102, 241, 0.18) !important;
    border-radius: 6px !important; color: #a5b4fc !important;
    font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important;
}

/* Radio */
.stRadio > div {
    display: flex !important;
    flex-direction: row !important;
    gap: 0.5rem !important;
    flex-wrap: wrap !important;
}
.stRadio > div > label {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.1rem !important;
    cursor: pointer !important;
    color: #71717a !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.78rem !important;
    transition: all 0.15s !important;
}
.stRadio > div > label:hover {
    border-color: rgba(99, 102, 241, 0.4) !important;
    color: #a5b4fc !important;
}

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3f3f46; }
</style>
""", unsafe_allow_html=True)


# ── Session state ───────────────────────────────────────────────────────────────
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())
if "indexed" not in st.session_state:
    st.session_state["indexed"] = False
if "input_type" not in st.session_state:
    st.session_state["input_type"] = "pdf"
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

session_id = st.session_state["session_id"]


def do_ingest(input_type, input_data):
    try:
        if input_type == "pdf":
            resp = requests.post(
                f"{API_BASE}/ingest/pdf",
                files={"file": (input_data.name, input_data.getvalue(), "application/pdf")},
                params={"session_id": session_id},
            )
        elif input_type == "link":
            resp = requests.post(
                f"{API_BASE}/ingest/link",
                json={"url": input_data, "session_id": session_id},
            )
        else:
            resp = requests.post(
                f"{API_BASE}/ingest/text",
                json={"content": input_data, "session_id": session_id},
            )
        if resp.status_code == 200:
            return True, resp.json().get("message", "Indexed successfully.")
        return False, resp.json().get("detail", resp.text)
    except requests.exceptions.ConnectionError:
        return False, f"Cannot connect to API at {API_BASE}. Is the backend running?"


def do_query(question):
    try:
        resp = requests.post(
            f"{API_BASE}/query",
            json={"question": question, "session_id": session_id},
        )
        if resp.status_code == 200:
            return resp.json()["answer"], None
        return None, resp.json().get("detail", resp.text)
    except requests.exceptions.ConnectionError:
        return None, f"Cannot connect to API at {API_BASE}."


# ── Hero ─────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">&#11043; Retrieval-Augmented Generation</div>
    <h1 class="hero-title">RAG<span>.</span>assistant</h1>
    <p class="hero-sub">Index a document &middot; Ask anything &middot; Get grounded answers</p>
</div>
""", unsafe_allow_html=True)

# ── Status bar ───────────────────────────────────────────────────────────────────
if st.session_state["indexed"]:
    st.markdown("""
    <div class="status-bar ready">
        <div class="status-dot green"></div>
        <span>Knowledge base ready &mdash; ask your questions below</span>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="status-bar waiting">
        <div class="status-dot blue"></div>
        <span>Awaiting data source &mdash; index a document to begin</span>
    </div>
    """, unsafe_allow_html=True)

# ── Step 1 ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="step-label"><span class="step-num">1</span> Choose source type</div>', unsafe_allow_html=True)

source_map = {"📄  PDF": "pdf", "🔗  URL": "link", "✍️  Text": "text"}
selected_label = st.radio(
    "source",
    list(source_map.keys()),
    index=list(source_map.values()).index(st.session_state["input_type"]),
    horizontal=True,
    label_visibility="collapsed",
)
st.session_state["input_type"] = source_map[selected_label]
input_type = st.session_state["input_type"]

st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

# ── Step 2 ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="step-label"><span class="step-num">2</span> Provide your content</div>', unsafe_allow_html=True)

input_data = None
if input_type == "pdf":
    input_data = st.file_uploader("Drop a PDF here or click to browse", type=["pdf"])
elif input_type == "link":
    input_data = st.text_input("Website URL", placeholder="https://example.com/article")
else:
    input_data = st.text_area("Paste or type your content", height=180, placeholder="Enter the text you want to query...")

st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

# ── Index button ──────────────────────────────────────────────────────────────────
col_btn, col_space = st.columns([1, 3])
with col_btn:
    index_clicked = st.button("⬡  Index Content", use_container_width=True)

if index_clicked:
    if not input_data:
        st.warning("Provide content before indexing.")
    else:
        with st.spinner("Embedding and indexing..."):
            ok, msg = do_ingest(input_type, input_data)
        if ok:
            st.session_state["indexed"] = True
            st.session_state["chat_history"] = []
            st.success(f"✓  {msg}")
        else:
            st.error(f"✗  {msg}")

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── Step 3: Q&A ───────────────────────────────────────────────────────────────────
st.markdown('<div class="step-label"><span class="step-num">3</span> Ask questions</div>', unsafe_allow_html=True)

if not st.session_state["indexed"]:
    st.info("Index a document above to unlock the Q&A interface.")
else:
    # Chat history
    if st.session_state["chat_history"]:
        history_html = ""
        for item in reversed(st.session_state["chat_history"]):
            history_html += f"""
            <div class="history-item">
                <div class="history-q">{item['q']}</div>
                <div class="history-a">{item['a']}</div>
            </div>"""
        st.markdown(f'<div class="panel">{history_html}</div>', unsafe_allow_html=True)

    q_col, btn_col = st.columns([5, 1])
    with q_col:
        question = st.text_input(
            "question",
            placeholder="What would you like to know about the content?",
            label_visibility="collapsed",
            key="question_input",
        )
    with btn_col:
        ask_clicked = st.button("Ask →", use_container_width=True)

    if ask_clicked:
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Retrieving and generating..."):
                answer, err = do_query(question)
            if answer:
                st.markdown(f"""
                <div class="answer-wrapper">
                    <div class="answer-header">&#11043; &nbsp;answer</div>
                    <div class="answer-body">{answer}</div>
                </div>
                """, unsafe_allow_html=True)
                st.session_state["chat_history"].append({"q": question, "a": answer})
            else:
                st.error(f"✗  {err}")

# ── Footer ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; margin-top:4rem; padding-top:1.5rem;
     border-top:1px solid rgba(255,255,255,0.05);">
    
</div>
""".format(sid=session_id[:8].upper()), unsafe_allow_html=True)