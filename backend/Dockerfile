FROM python:3.11-slim

WORKDIR /app

# System deps (curl needed to install Ollama)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Ollama (local models) ──────────────────────────────────────────────
# Install the Ollama binary and bake a small Llama model into the image so
# the "ollama" provider works out of the box (no runtime download).
RUN curl -fsSL https://ollama.com/install.sh | sh

ENV OLLAMA_MODELS=/app/ollama_models
RUN mkdir -p /app/ollama_models && chmod -R 777 /app/ollama_models
RUN (ollama serve > /tmp/ollama_build.log 2>&1 &) && \
    sleep 6 && \
    (for i in $(seq 1 30); do ollama list >/dev/null 2>&1 && break; sleep 1; done) && \
    ollama pull llama3.2:1b && \
    echo "Baked llama3.2:1b into image"

# App code
COPY . .

# Writable, world-accessible dirs for ephemeral data (HF Spaces runtime).
# Durable data (users, RAG) lives in PostgreSQL via DATABASE_URL.
RUN mkdir -p /tmp/appdata/workspace /tmp/appdata/vectordb /tmp/appdata/ragdb \
    /tmp/appdata/cache /tmp/appdata/workflows && chmod -R 777 /tmp/appdata \
    && chmod +x /app/start.sh

# Hugging Face Spaces expects the app on port 7860.
ENV PORT=7860 \
    WORKSPACE_PATH=/tmp/appdata/workspace \
    MEMORY_DB_PATH=/tmp/appdata/memory.db \
    VECTOR_DB_PATH=/tmp/appdata/vectordb \
    RAG_DB_PATH=/tmp/appdata/ragdb \
    CACHE_DB_PATH=/tmp/appdata/cache \
    WORKFLOWS_PATH=/tmp/appdata/workflows \
    AUTH_DB_PATH=/tmp/appdata/auth.db \
    HF_HOME=/tmp/hf \
    ENABLE_OLLAMA=true \
    OLLAMA_MODEL=llama3.2:1b \
    OLLAMA_BASE_URL=http://127.0.0.1:11434

EXPOSE 7860

CMD ["bash", "start.sh"]
