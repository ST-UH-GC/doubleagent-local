#!/bin/bash
# Switch DoubleAgent between Ollama (local) and Claude (Anthropic API)
# Usage: ./switch.sh ollama
#        ./switch.sh claude

set -e

if [ "$1" = "claude" ]; then
  PROVIDER="anthropic"
  LABEL="Claude (Anthropic API)"
elif [ "$1" = "ollama" ]; then
  PROVIDER="ollama"
  LABEL="Ollama (local)"
else
  echo "Usage: ./switch.sh ollama | claude"
  exit 1
fi

# Update provider in docker-compose.yml (no git branch switching needed)
sed -i '' "s/DA_PROVIDER=.*/DA_PROVIDER=$PROVIDER/" docker-compose.yml
sed -i '' "s/VITE_PROVIDER=.*/VITE_PROVIDER=$PROVIDER/" docker-compose.yml

docker-compose up --build -d

echo ""
echo "✅ Switched to $LABEL"
echo "   Open: http://localhost:5173"
