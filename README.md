<div align="center">

# 🪐 Nexus AI — Multi-Agent Task Automation Platform

**An autonomous, multi-agent AI system with Retrieval-Augmented Generation (RAG), long-term vector memory, visual workflow automation, and scheduled execution.**

[![Backend](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Frontend](https://img.shields.io/badge/Frontend-Next.js%2014-000000?logo=nextdotjs&logoColor=white)](https://nextjs.org/)
[![LLM](https://img.shields.io/badge/LLM-Claude%20%7C%20GPT%20%7C%20Gemini-8B5CF6)](https://www.anthropic.com/)
[![Vector%20DB](https://img.shields.io/badge/Vector%20DB-ChromaDB-FF6F61)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](#-license)

</div>

---

## 📖 Abstract

**Nexus AI** is a final-year engineering project that demonstrates an end-to-end *agentic AI* platform. Unlike a single chatbot, it uses an **orchestrator–worker multi-agent architecture** in which a coordinating agent decomposes a user request into sub-tasks and delegates them to specialised agents (research, coding, analysis, execution). Each agent has access to a sandboxed toolbelt — web search, code execution, file management, APIs, and more.

The system is grounded in the user's own data through a **Retrieval-Augmented Generation (RAG)** pipeline: documents are chunked, embedded with a sentence-transformer model, stored in a **ChromaDB** vector database, and retrieved at query time to give the LLM accurate, source-backed context. The platform also features **JWT authentication**, **long-term semantic memory**, a **visual workflow builder**, **task scheduling**, and **cost/usage analytics**, served through a modern Next.js interface and deployed on the cloud (Render + Vercel + PostgreSQL).

---

## ✨ Key Features

| Category | Highlights |
|----------|------------|
| 🤖 **Multi-Agent System** | Orchestrator decomposes tasks and delegates to Researcher, Coder, Analyst & Executor agents |
| 📚 **RAG Pipeline** | Upload PDF/TXT/MD/HTML → chunk → embed → ChromaDB → retrieve relevant context per query |
| 🧠 **Long-Term Memory** | Vector memory + conversation memory + a structured knowledge base |
| 🔌 **15+ Tools** | Web search/browse, code & shell execution, file ops, API calls, PDF reading, email, and more |
| 🔀 **Multi-LLM Support** | Anthropic Claude, OpenAI GPT, Google Gemini, and local Ollama — with automatic fallback |
| 🛠️ **Visual Workflows** | Drag-and-drop workflow builder (React Flow) with agent, tool, condition & loop nodes |
| ⏰ **Scheduling** | Run workflows on cron / interval / date triggers |
| 🔐 **Auth & Security** | JWT access/refresh tokens, role-based access, rate limiting, human-in-the-loop for dangerous actions |
| 📊 **Analytics** | Token usage, cost tracking per provider/model, and an agent activity timeline |
| 🎨 **Premium UI** | Next.js 14 + Tailwind, dark mode, streaming-style chat, markdown & code rendering |

---

## 🏛️ System Architecture

```
                         ┌──────────────────────────────┐
                         │        User (Browser)         │
                         │   Next.js 14 + Tailwind UI    │
                         └───────────────┬──────────────┘
                                         │  HTTPS / JWT
                                         ▼
        ┌────────────────────────────────────────────────────────────┐
        │                    FastAPI Backend (async)                  │
        │  Auth · Rate Limiting · CORS · REST + WebSocket             │
        └───────┬───────────────────┬───────────────────┬────────────┘
                │                   │                   │
                ▼                   ▼                   ▼
     ┌────────────────┐   ┌──────────────────┐  ┌───────────────────┐
     │  RAG Pipeline  │   │  Orchestrator    │  │  Workflow Engine  │
     │  (ChromaDB +   │   │     Agent        │  │   + Scheduler     │
     │  embeddings)   │   └────────┬─────────┘  └───────────────────┘
     └───────┬────────┘            │ delegates
             │ context     ┌───────┼────────┬──────────┐
             │             ▼       ▼        ▼          ▼
             │       ┌─────────┐┌───────┐┌────────┐┌──────────┐
             └──────▶│Research ││ Coder ││Analyst ││ Executor │
                     │  Agent  ││ Agent ││ Agent  ││  Agent   │
                     └────┬────┘└───┬───┘└───┬────┘└────┬─────┘
                          └─────────┴────────┴──────────┘
                                      │  tool calls
                                      ▼
                     ┌────────────────────────────────────┐
                     │  Toolbelt: web · code · files · API │
                     │  · shell · pdf · email · database   │
                     └────────────────────────────────────┘
                                      │
                                      ▼
         ┌──────────────────────────────────────────────────────────┐
         │  Persistence:  PostgreSQL/SQLite · ChromaDB · File store  │
         └──────────────────────────────────────────────────────────┘
```

---

## 🔎 How the RAG Pipeline Works

Retrieval-Augmented Generation grounds the LLM in **your** documents instead of relying only on its training data.

```
 Upload ──▶ Extract text ──▶ Chunk (800 chars, 150 overlap) ──▶ Embed ──▶ Store in ChromaDB
 (PDF/TXT/MD/HTML)      (PyPDF2 / BeautifulSoup)    (all-MiniLM-L6-v2)

 User asks a question ──▶ Embed query ──▶ Vector similarity search ──▶ Top-k chunks
                                                                          │
        LLM answer  ◀── Augmented prompt (context + question)  ◀──────────┘
```

1. **Ingestion** — A document is uploaded, its text extracted, then split into overlapping chunks that preserve sentence/paragraph boundaries.
2. **Embedding** — Each chunk is converted to a vector using the `all-MiniLM-L6-v2` sentence-transformer.
3. **Storage** — Vectors + metadata are persisted in ChromaDB.
4. **Retrieval** — At chat time the question is embedded and the most semantically similar chunks are fetched.
5. **Augmentation** — Retrieved context is prepended to the prompt so the agent answers from source material, reducing hallucination.

> Try it: open **Documents**, upload a file, then ask a question in **Chat** — answers are grounded in your upload, and a *“N docs in context”* badge appears.

---

## 🧰 Tech Stack

**Backend** — FastAPI · Pydantic · SQLAlchemy + asyncpg · ChromaDB · sentence-transformers · APScheduler · Anthropic / OpenAI / Gemini / Ollama SDKs · python-jose (JWT) · Uvicorn

**Frontend** — Next.js 14 (App Router) · TypeScript · Tailwind CSS · Zustand · React Flow · Recharts · React Markdown · Lucide Icons · Framer Motion

**Infrastructure** — Render (backend) · Render PostgreSQL · Vercel (frontend) · Docker

---

## 📁 Project Structure

```
ai-task-agent/
├── backend/
│   ├── main.py                 # FastAPI entry point & component wiring
│   ├── config.py               # Pydantic settings
│   ├── agents/                 # Multi-agent system
│   │   ├── orchestrator.py     #   coordinator / task decomposition
│   │   ├── researcher.py  coder.py  analyst.py  executor.py
│   │   └── base_agent.py
│   ├── rag/                    # ── RAG pipeline ──
│   │   ├── rag_pipeline.py     #   ChromaDB ingest / query / context
│   │   └── document_processor.py  # chunking & text extraction
│   ├── tools/                  # 15+ sandboxed tools
│   ├── memory/                 # vector memory · conversation · knowledge base
│   ├── llm/                    # provider abstraction + cost tracker
│   ├── workflows/              # engine · manager · scheduler
│   ├── auth/                   # JWT auth, users, API keys
│   ├── database/               # SQLAlchemy models & async connection
│   ├── middleware/             # rate limiting
│   └── api/                    # REST routes + WebSocket
├── frontend/
│   ├── app/                    # Next.js routes (auth + dashboard)
│   ├── components/             # ChatInterface, Dashboard, WorkflowBuilder…
│   └── lib/                    # api client, store (Zustand), types
├── render.yaml                 # Render deployment blueprint
└── README.md
```

---

## 🚀 Getting Started (Local)

### Prerequisites
- Python **3.11**, Node.js **18+**
- An API key for at least one provider (Anthropic recommended) — or Ollama installed locally

### 1 · Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS / Linux

pip install -r requirements.txt
cp .env.example .env            # then edit .env with your keys

python main.py                 # serves on http://localhost:8000
```

### 2 · Frontend
```bash
cd frontend
npm install
# point the UI at your backend:
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
npm run dev                     # http://localhost:3000
```

### 3 · Open the app
- **App:** http://localhost:3000
- **Interactive API docs (Swagger):** http://localhost:8000/docs

---

## 🔑 Configuration

All settings live in `backend/.env` (see [`.env.example`](backend/.env.example)). The essentials:

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
JWT_SECRET=<long-random-string>
# DATABASE_URL=postgresql://...   # omit for local SQLite
```

The frontend reads a single variable, `NEXT_PUBLIC_API_URL`, pointing to the backend.

---

## 📡 API Reference

> Base path: `/api/v1` — full interactive docs at `/docs`.

**Auth**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create an account |
| POST | `/auth/login` | Obtain access + refresh tokens |
| POST | `/auth/refresh` | Refresh access token |
| GET  | `/auth/me` | Current user profile |
| GET  | `/auth/usage` | User usage quota & stats |

**Chat & RAG**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat` | Send a message to the agent system (RAG-augmented) |
| POST | `/chat/clear` | Clear conversation memory |
| POST | `/rag/ingest` | Upload a document into the vector store |
| GET  | `/rag/documents` | List ingested documents |
| DELETE | `/rag/documents/{id}` | Remove a document |
| POST | `/rag/query` | Semantic search over documents |
| GET  | `/rag/stats` | Vector store statistics |

**Memory · Workflows · Tools · Analytics**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/memory/*`, `/knowledge/*` | Vector memory & knowledge base |
| GET/POST/DELETE | `/workflows/*` | Create / list / run / delete workflows |
| GET/POST | `/schedule/*` | Schedule, pause, resume, cancel tasks |
| GET/POST | `/tools`, `/tools/{name}/execute` | List & invoke tools |
| GET | `/analytics/usage`, `/analytics/costs`, `/analytics/providers` | Usage & cost analytics |

---

## ☁️ Deployment

This project is deployed with a three-tier cloud setup:

| Layer | Service | Notes |
|-------|---------|-------|
| Frontend | **Vercel** | Set `NEXT_PUBLIC_API_URL` to the backend URL |
| Backend | **Render** (Web Service) | Python 3.11; see [`render.yaml`](render.yaml) |
| Database | **Render PostgreSQL** | `DATABASE_URL` injected as an env var |

Render build & start commands:
```bash
# Build — pre-downloads the embedding model so first request is fast
pip install -r requirements.txt && \
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Start — asyncio loop avoids uvloop/nest-asyncio conflicts
uvicorn main:app --host 0.0.0.0 --port $PORT --loop asyncio
```

---

## 🔐 Security

- **JWT** access/refresh tokens with configurable expiry
- **Role-based access control** (admin vs user) and per-user usage quotas
- **Rate limiting** middleware (per-minute / per-hour / burst)
- **Human-in-the-loop** confirmation for dangerous tools (shell, file delete, email)
- **Sandboxed** code/shell execution with timeouts and memory limits

---

## 🗺️ Roadmap

- [ ] Token-level streaming responses over WebSocket
- [ ] Per-document citations in chat answers
- [ ] Hybrid (keyword + vector) retrieval and re-ranking
- [ ] Collaborative multi-user workspaces
- [ ] Plugin SDK for custom tools

---

## 📄 License

Released under the **MIT License** — free to use, study, and extend.

<div align="center">
<sub>Built as a final-year engineering project demonstrating agentic AI, RAG, and full-stack cloud deployment.</sub>
</div>
