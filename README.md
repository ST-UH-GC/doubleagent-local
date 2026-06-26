# DoubleAgent — Local Edition

DoubleAgent is a tool for running two AI chatbots side by side, watching them converse, debate, or explore a topic together. Each bot gets its own system prompt and persona — you set the stage, they do the talking.

## Background

DoubleAgent was originally built as a software engineering student project (OHTU, University of Helsinki) commissioned by a researcher at the university. The student team delivered a fully working application. This repository is a personal local fork, adapted for everyday use without any institutional infrastructure — no servers, no cloud databases, no accounts required.

## Two modes

| Mode | Branch | Models | Requires |
|---|---|---|---|
| **Ollama** | `main` | Local models (Qwen 3 14B etc.) | Ollama installed |
| **Claude** | `anthropic-api` | Claude Sonnet / Haiku / Opus | Anthropic API key |

Switch between them with the Desktop shortcuts, or from Terminal:

```bash
./switch.sh ollama   # local models, no cost
./switch.sh claude   # Anthropic API
```

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Ollama](https://ollama.com) (for the `main` branch)

## Getting started

### Ollama (main branch)

1. Install Ollama and pull a model:
   ```bash
   ollama pull qwen3:14b
   ```
2. Start the app:
   ```bash
   ./switch.sh ollama
   ```
3. Open **http://localhost:5173**

### Claude API (anthropic-api branch)

1. Get an API key from [console.anthropic.com](https://console.anthropic.com)
2. Add it to `backend/.env`:
   ```bash
   echo "ANTHROPIC_API_KEY=your-key-here" > backend/.env
   ```
3. Start the app:
   ```bash
   ./switch.sh claude
   ```
4. Open **http://localhost:5173**

## Running

```bash
# Start (background, quiet)
docker-compose up --build -d

# Stop
docker-compose down

# View logs
docker-compose logs -f
```

After the first build, you can drop `--build` for faster startup.

## Data

Conversations and saved prompts are stored in `backend/data/doubleagent.db` (SQLite). The file lives on your Mac and persists across restarts and branch switches. It is gitignored and never uploaded anywhere.

## Project structure

```
doubleagent-local/
├── backend/          # FastAPI + LangGraph + SQLAlchemy
│   ├── app/
│   │   ├── main.py       # API endpoints
│   │   ├── chatbot.py    # LLM integration (Ollama or Anthropic)
│   │   └── db/           # SQLite models and database setup
│   └── data/             # SQLite database (gitignored)
├── frontend/         # React 19 + Vite + TailwindCSS
│   └── src/
│       ├── App.jsx
│       ├── components/
│       ├── contexts/     # BotConfigContext, ChatSessionContext
│       └── pages/
├── switch.sh         # Branch/mode switcher
└── docker-compose.yml
```
