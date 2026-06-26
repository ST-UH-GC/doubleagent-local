# DoubleAgent — Local Edition

DoubleAgent is a tool for running two AI chatbots side by side, watching them converse, debate, or explore a topic together. Each bot gets its own system prompt and persona — you set the stage, they do the talking.

## Background

DoubleAgent was originally built as a software engineering student project (OHTU, University of Helsinki) commissioned by a researcher at the university. The student team delivered a fully working application. This repository is a personal local fork, adapted for everyday use without any institutional infrastructure — no servers, no cloud databases, no accounts required.

## Two modes, one branch

The app runs in two modes, switchable at any time with a Desktop shortcut or a single command. No git branch switching, no reinstalling — one Docker image handles both.

| Mode | Models | Requires |
|---|---|---|
| **Ollama** | Local models (Qwen 3 14B etc.) | Ollama installed + model pulled |
| **Claude** | Claude Sonnet / Haiku / Opus | Anthropic API key in `backend/.env` |

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com) — for local model mode

## Getting started

### Ollama mode (no API key needed)

1. Install Ollama and pull a model:
   ```bash
   ollama pull qwen3:14b
   ```
2. Double-click **`DoubleAgent - Ollama`** on your Desktop, or run:
   ```bash
   cd /Users/tkalcan/Claude_Code/doubleagent-local
   ./switch.sh ollama
   ```
3. Open **http://localhost:5173**

### Claude mode (Anthropic API)

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Add it to `backend/.env` (run in Terminal):
   ```bash
   echo "ANTHROPIC_API_KEY=your-key-here" > /Users/tkalcan/Claude_Code/doubleagent-local/backend/.env
   ```
3. Double-click **`DoubleAgent - Claude`** on your Desktop, or run:
   ```bash
   ./switch.sh claude
   ```
4. Open **http://localhost:5173**

## Switching modes

```bash
./switch.sh ollama   # switch to local Ollama models
./switch.sh claude   # switch to Claude API
```

Or use the Desktop shortcuts. Each switch rebuilds the container with the correct provider — takes about a minute.

## Other commands

```bash
# Stop the app
docker-compose down

# View live logs
docker-compose logs -f

# Start without rebuilding (faster, if nothing changed)
docker-compose up -d
```

## Data

Conversations and saved prompts are stored in `backend/data/doubleagent.db` (SQLite). The file lives on your Mac and persists across restarts and mode switches. It is gitignored and never uploaded anywhere.

## Project structure

```
doubleagent-local/
├── backend/
│   ├── app/
│   │   ├── main.py        # API endpoints
│   │   ├── chatbot.py     # LLM integration (Ollama or Anthropic, via DA_PROVIDER)
│   │   └── db/            # SQLite models and setup
│   ├── data/              # SQLite database (gitignored)
│   └── .env               # API keys (gitignored)
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── components/    # Including ModelSelection (reads VITE_PROVIDER)
│       └── contexts/      # BotConfigContext, ChatSessionContext
├── switch.sh              # Mode switcher (ollama | claude)
├── docker-compose.yml     # DA_PROVIDER + VITE_PROVIDER set here
└── CHANGELOG.md
```
