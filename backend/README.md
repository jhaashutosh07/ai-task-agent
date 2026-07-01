---
title: Nexus AI Backend
emoji: 🪐
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Nexus AI — Backend

FastAPI backend for the Nexus AI multi-agent platform (chat, RAG with citations,
streaming, workflows, auth). Deployed as a Docker Space.

Configuration is provided via Space **Secrets / Variables**:

- `OPENAI_API_KEY` — required (LLM + embeddings)
- `LLM_PROVIDER` — `openai`
- `JWT_SECRET` — auth signing secret
- `DATABASE_URL` — PostgreSQL connection string (durable users + RAG)
- `ANTHROPIC_API_KEY` / `GOOGLE_API_KEY` — optional fallback providers

Health check: `/health` · API docs: `/docs`
