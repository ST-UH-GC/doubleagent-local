#!/bin/bash
# Switch between Ollama (local) and Claude (Anthropic API) modes
# Usage: ./switch.sh ollama
#        ./switch.sh claude

if [ "$1" = "claude" ]; then
  git checkout anthropic-api
elif [ "$1" = "ollama" ]; then
  git checkout main
else
  echo "Usage: ./switch.sh ollama | claude"
  exit 1
fi

docker-compose up --build -d
echo "✅ Switched to $1 — open http://localhost:5173"
