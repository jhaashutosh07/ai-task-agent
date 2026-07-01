#!/usr/bin/env bash
# Launch the local Ollama server (best-effort) next to the FastAPI app so the
# "ollama" provider works even on a cloud host. The API still starts regardless.
export OLLAMA_MODELS="${OLLAMA_MODELS:-/app/ollama_models}"
export OLLAMA_HOST="127.0.0.1:11434"
export OLLAMA_KEEP_ALIVE="-1"           # keep the model resident (no cold reloads)
MODEL="${OLLAMA_MODEL:-llama3.2:1b}"

if command -v ollama >/dev/null 2>&1; then
  echo "Starting Ollama server…"
  ollama serve > /tmp/ollama.log 2>&1 &
  # Pre-warm the model in the background so the first request is fast.
  (
    for i in $(seq 1 40); do
      curl -s http://127.0.0.1:11434/api/tags >/dev/null 2>&1 && break
      sleep 1
    done
    curl -s http://127.0.0.1:11434/api/generate \
      -d "{\"model\":\"$MODEL\",\"prompt\":\"hi\",\"stream\":false,\"keep_alive\":-1}" >/dev/null 2>&1
    echo "Ollama model '$MODEL' warmed and pinned in memory."
  ) &
fi

exec uvicorn main:app --host 0.0.0.0 --port 7860 --loop asyncio
