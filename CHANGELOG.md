# DoubleAgent Local — Change Log

## 2026-06-26 — Initial local fork (Claude Code session with tkalcan)

### Context
DoubleAgent was a fully working OHTU student project. After the project ended, the app was no longer accessible for personal use. This session created a personal local fork, stripped of institutional dependencies, runnable on a single Mac with no external services.

---

### What was done

#### Authentication removed
- Removed all OIDC/university SSO login code (`oidc_router.py` deleted)
- Removed `SessionMiddleware` and all session-based auth logic from `backend/app/main.py`
- Replaced `get_current_user()` and `get_user_id()` dependencies with stubs that return a fixed local user — all API endpoints continue working unchanged
- Removed the Logout button and `LoginPage` from the frontend
- App now opens directly to the chat UI

#### Database switched from Supabase/PostgreSQL to SQLite
- `backend/app/db/database.py`: defaults to `sqlite:///./data/doubleagent.db`
- `backend/app/main.py`: calls `Base.metadata.create_all()` on startup — no migrations needed
- Database file lives at `backend/data/doubleagent.db`, persists across restarts
- `backend/data/` added to `.gitignore` so data is never committed or branch-switched away

#### AI provider: two branches

**`main` branch — Ollama (local, free)**
- Swapped `langchain-openai` (Azure) for `langchain-ollama`
- `chatbot.py` uses `ChatOllama` pointing to `http://host.docker.internal:11434`
- Model: `qwen3:14b` (best fit for M2 Max 32 GB)
- No API key required

**`anthropic-api` branch — Claude (Anthropic API)**
- Swapped `langchain-ollama` for `langchain-anthropic`
- `chatbot.py` uses `ChatAnthropic` with key from `backend/.env`
- Models: Claude Sonnet, Haiku, Opus
- API key stored in `backend/.env` (gitignored, never committed)

#### Dependencies cleaned up
- Removed: `authlib`, `itsdangerous`, `psycopg2-binary`, `langchain-openai`
- Added: `langchain-ollama` (main) / `langchain-anthropic` (anthropic-api)
- `Dockerfile.dev`: added `poetry lock --no-update` step so lock file stays in sync automatically on build

#### Developer experience
- `switch.sh` — one-command branch switcher (`./switch.sh ollama` or `./switch.sh claude`)
- Two Desktop shortcuts: `DoubleAgent - Ollama.command` and `DoubleAgent - Claude.command`
  - Double-click to switch mode and start the app, no Terminal knowledge needed
- Docker runs in detached mode (`-d`) — terminal stays clean
- README rewritten to reflect the local fork

#### Repository
- New GitHub repo: https://github.com/ST-UH-GC/doubleagent-local
- Fresh git history (original OHTU repo history not carried over)
- Two branches: `main` (Ollama) and `anthropic-api` (Claude)

---

### File map of changes from original OHTU project

| File | Change |
|---|---|
| `backend/app/main.py` | Auth removed, user stubbed, CORS unconditional, DB auto-init added |
| `backend/app/db/database.py` | SQLite default, NullPool removed |
| `backend/app/chatbot.py` | AI provider swapped (per branch) |
| `backend/pyproject.toml` | Dependencies updated (per branch) |
| `backend/Dockerfile.dev` | `poetry lock --no-update` added, `libpq-dev` removed |
| `backend/.env` | Created locally (gitignored) |
| `backend/data/` | Created for SQLite persistence (gitignored) |
| `docker-compose.yml` | OLLAMA_BASE_URL / ANTHROPIC_API_KEY added, data volume mounted |
| `frontend/src/App.jsx` | Auth gate removed, always renders HomePage |
| `frontend/src/components/Menu.jsx` | Logout button removed |
| `frontend/src/components/ModelSelection.jsx` | Model list updated per branch |
| `backend/app/routers/oidc_router.py` | **Deleted** |
| `frontend/src/pages/LoginPage.jsx` | **Deleted** |
| `switch.sh` | **New** — branch/mode switcher script |
| `CHANGELOG.md` | **New** — this file |
| `README.md` | Rewritten for local fork |
