FROM python:3.11-slim

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Writable, world-accessible dirs for ephemeral data (HF Spaces runtime).
# Durable data (users, RAG) lives in PostgreSQL via DATABASE_URL.
RUN mkdir -p /tmp/appdata/workspace /tmp/appdata/vectordb /tmp/appdata/ragdb \
    /tmp/appdata/cache /tmp/appdata/workflows && chmod -R 777 /tmp/appdata

# Hugging Face Spaces expects the app on port 7860.
ENV PORT=7860 \
    WORKSPACE_PATH=/tmp/appdata/workspace \
    MEMORY_DB_PATH=/tmp/appdata/memory.db \
    VECTOR_DB_PATH=/tmp/appdata/vectordb \
    RAG_DB_PATH=/tmp/appdata/ragdb \
    CACHE_DB_PATH=/tmp/appdata/cache \
    WORKFLOWS_PATH=/tmp/appdata/workflows \
    AUTH_DB_PATH=/tmp/appdata/auth.db \
    HF_HOME=/tmp/hf

EXPOSE 7860

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860", "--loop", "asyncio"]
