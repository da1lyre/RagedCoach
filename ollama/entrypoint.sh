#!/bin/bash
set -e

ollama serve &
OLLAMA_PID=$!

for i in $(seq 1 30); do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# тянем модель
ollama pull qwen3:0.6b

wait $OLLAMA_PID