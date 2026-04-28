<p align="center">
  <h1 align="center">⬡ RAG.assistant</h1>
  <p align="center">
    <strong>An advanced Retrieval-Augmented Generation system with streaming responses, conversation memory, and source citations.</strong>
  </p>
  <p align="center">
    <a href="#features">Features</a> •
    <a href="#demo">Demo</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#api-reference">API Reference</a> •
    <a href="#deployment">Deployment</a> •
    <a href="#tech-stack">Tech Stack</a>
  </p>
</p>

---

## Features

| Feature | Description |
|---------|-------------|
| 📄 **Multi-Source Ingestion** | Index PDFs, URLs, and raw text — multiple sources per session |
| 🔥 **Streaming Responses** | Token-by-token streaming via NDJSON for real-time answers |
| 💬 **Conversation Memory** | Follow-up questions with context from the last 5 conversation turns |
| 📎 **Source Citations** | Expandable cards showing which document chunks grounded each answer |
| ⚙️ **Model Configuration** | Switch between Llama 3, Mixtral, Gemma models + adjust temperature |
| 🎯 **MMR Retrieval** | Maximum Marginal Relevance search for diverse, high-quality results |
| 📥 **Export Chat** | Download your full conversation as a Markdown file |
| 🐳 **Docker Ready** | One-command deployment with Docker Compose |

## Architecture

```
┌──────────────────┐         ┌──────────────────────────────┐
│                  │  HTTP   │         FastAPI Backend       │
│    Streamlit     │ ──────► │                              │
│    Frontend      │ ◄────── │  /ingest/*   → Loader        │
│                  │   SSE   │  /query/*    → RAG Chain      │
│  • Chat UI       │         │  /session/*  → Session Mgmt   │
│  • Model Config  │         │                              │
│  • Source Cards  │         │  ┌────────┐   ┌───────────┐  │
│                  │         │  │ChromaDB│   │ Groq LLM  │  │
└──────────────────┘         │  │(Vector)│   │(Inference)│  │
                             │  └────────┘   └───────────┘  │
                             └──────────────────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- A [Groq API key](https://console.groq.com/keys) (free tier available)

### 1. Clone & Install

```bash
git clone https://github.com/madhavzer0oo0/RAG_assistant.git
cd RAG_assistant
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your Groq API key:

```env
GROQ_API_KEY=gsk_your_key_here
LLM_MODEL=llama3-8b-8192
EMBEDDING_MODEL=all-MiniLM-L6-v2
API_BASE_URL=http://localhost:8000
```

### 3. Run

**Terminal 1 — Backend:**

```bash
python -m uvicorn main:app --port 8000
```

**Terminal 2 — Frontend:**

```bash
streamlit run app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

### Docker (Alternative)

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Frontend: http://localhost:8501

## Usage

1. **Choose a source type** — PDF, URL, or plain text
2. **Index your content** — click "Index Content" to embed and store it
3. **Ask questions** — use the chat input to query your knowledge base
4. **View sources** — expand the "source chunks referenced" under each answer
5. **Configure** — use the sidebar to switch models or adjust temperature

> 💡 **Tip:** You can index multiple documents into the same session to build a richer knowledge base.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/health` | Status & active sessions |
| `GET` | `/models` | List available LLM models |
| `POST` | `/ingest/pdf` | Upload & index a PDF |
| `POST` | `/ingest/link` | Scrape & index a URL |
| `POST` | `/ingest/text` | Index raw text |
| `POST` | `/query` | Ask a question (returns full response) |
| `POST` | `/query/stream` | Ask a question (streaming NDJSON) |
| `GET` | `/session/{id}/sources` | List ingested sources |
| `GET` | `/session/{id}/history` | Get chat history |
| `POST` | `/session/{id}/config` | Update model / temperature |
| `DELETE` | `/session/{id}` | Clear session data |
| `GET` | `/session/{id}/export` | Export chat as Markdown |

### Example — Index & Query

```bash
# Index a URL
curl -X POST http://localhost:8000/ingest/link \
  -H "Content-Type: application/json" \
  -d '{"url": "https://en.wikipedia.org/wiki/Retrieval-augmented_generation", "session_id": "demo"}'

# Ask a question
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG?", "session_id": "demo"}'
```

## Deployment

### Render (Backend — Free Tier)

1. Push your repo to GitHub
2. Go to [render.com](https://render.com) → **New** → **Web Service**
3. Connect your repo and configure:
   - **Build Command:** `pip install -r requirements.txt && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add environment variable: `GROQ_API_KEY` = your key
5. Deploy

### Streamlit Cloud (Frontend — Free)

1. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Connect your GitHub repo, set main file to `app.py`
3. In **Advanced Settings → Secrets**, add:
   ```toml
   API_BASE_URL = "https://your-render-url.onrender.com"
   ```
4. Deploy

### Render Blueprint (Both Services)

The included `render.yaml` supports one-click Blueprint deployment:

1. Go to Render → **New** → **Blueprint**
2. Connect your repo — Render auto-detects `render.yaml`
3. Set the required environment variables when prompted

> **Note:** Render free tier sleeps after 15 min of inactivity. First request after sleep takes ~30–60s for model loading.

## Project Structure

```
rag/
├── rag/                    # Core RAG pipeline
│   ├── embeddings.py       # Sentence-transformer wrapper (singleton cached)
│   ├── loader.py           # PDF / URL / text document loading
│   ├── rag_chain.py        # LLM chain with memory, streaming, citations
│   ├── splitter.py         # Recursive text chunking
│   └── vectorstore.py      # ChromaDB vector store (append-capable)
├── main.py                 # FastAPI backend (14 endpoints)
├── app.py                  # Streamlit frontend (chat UI)
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container image
├── docker-compose.yml      # Multi-service orchestration
├── render.yaml             # Render Blueprint config
├── .env.example            # Environment template
└── .gitignore
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **LLM** | [Groq](https://groq.com) (Llama 3, Mixtral, Gemma) |
| **Embeddings** | [Sentence Transformers](https://www.sbert.net/) (`all-MiniLM-L6-v2`) |
| **Vector Store** | [ChromaDB](https://www.trychroma.com/) |
| **Orchestration** | [LangChain](https://www.langchain.com/) |
| **Backend** | [FastAPI](https://fastapi.tiangolo.com/) + Uvicorn |
| **Frontend** | [Streamlit](https://streamlit.io/) |
| **Deployment** | Docker · Render · Streamlit Cloud |

## Available Models

| Model | Context Window | Best For |
|-------|---------------|----------|
| `llama3-8b-8192` | 8K tokens | Fast, general-purpose (default) |
| `llama3-70b-8192` | 8K tokens | Higher accuracy, slower |
| `mixtral-8x7b-32768` | 32K tokens | Long documents |
| `gemma2-9b-it` | 8K tokens | Instruction-following tasks |

## License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ using LangChain, Groq, and Streamlit
</p>
