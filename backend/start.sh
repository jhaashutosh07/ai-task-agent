#!/usr/bin/env bash
# Launch the local Ollama server (best-effort) next to the FastAPI app so the
# "ollama" provider works even on a cloud host. The API still starts regardless.
export OLLAMA_MODELS="${OLLAMA_MODELS:-/app/ollama_models}"
export OLLAMA_HOST="127.0.0.1:11434"

if command -v ollama >/dev/null 2>&1; then
  echo "Starting Ollama server (models dir: $OLLAMA_MODELS)…"
  ollama serve > /tmp/ollama.log 2>&1 &
fi

exec uvicorn main:app --host 0.0.0.0 --port 7860 --loop asyncio
