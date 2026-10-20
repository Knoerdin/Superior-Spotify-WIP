# Quick Start

## What Exists Today

This project is in the **planning phase**. There is no runnable application.

What you can do right now:

| Do this | Where |
|---|---|
| Read the plan of record | `planning/comprehensive-plan.md` |
| Read how agents work in this repo | `AGENTS.md` |
| Read the architecture | `planning/architecture.md` |
| Review the stack options | `planning/tech-stack.md` |
| Review the intended layout | `planning/project-structure.md` |
| Read the deep docs | `docs/ml/smart-shuffle.md`, `docs/backend/foundation.md`, `docs/api-integration/spotify.md`, `docs/security/oauth.md` |
| See the UI mockup | `Sketches/Home Screen sketch.jpg` |

What you cannot do: run the app, run tests, or start a database. None of those files exist yet.

## When Implementation Begins (PLANNED)

Everything in this section describes files and commands that **do not exist yet**. They come from the plan in `planning/project-structure.md`. Verify each item exists before running it.

### Expected prerequisites (PLANNED)

- Python 3.11+
- Docker (for PostgreSQL and Redis)
- A Spotify Premium account

### Expected setup (PLANNED, files not yet created)

1. **Infrastructure** (expects a `docker-compose.yml` that does not exist yet):

   ```bash
   docker-compose up -d   # PostgreSQL on 5432, Redis on 6379
   ```

2. **Python environment** (expects `requirements.txt`, not yet created):

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configuration** (expects `.env.example`, not yet created):

   ```bash
   cp .env.example .env
   ```

   Then edit `.env`:

   1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   2. Create a new application
   3. Copy Client ID and Client Secret into `.env`
   4. Set the Redirect URI to `http://localhost:8000/callback`

4. **Server** (expects `app/main.py`, not yet created):

   ```bash
   uvicorn app.main:app --reload
   ```

   The API would then be available at `http://localhost:8000`, with Swagger docs at `http://localhost:8000/docs`.

5. **Tests and migrations** (expect `tests/` content and Alembic, not yet created):

   ```bash
   pytest
   alembic revision --autogenerate -m "description"
   alembic upgrade head
   ```

### Expected first run flow (PLANNED)

1. Visit `/auth/login` to authenticate with Spotify
2. Land on the dashboard after authentication
3. Start capturing listening events (self-tracking is mandatory; Spotify only returns 20 to 50 recent tracks)

## Before Building: Open Decisions

Resolve these in `/spec` before the first implementation phase:

1. **Frontend**: HTMX/Jinja2 (Option 1 in `planning/tech-stack.md`), Next.js/Nuxt, or Streamlit. The docs disagree and nothing is chosen yet.
2. **Schema counts**: 8 core tables and 12 audio features (union per `AGENTS.md`). `CLAUDE.md` and `.claude/agents/CONTEXT.md` historically disagreed; lock the numbers in the spec.
3. **Smart shuffle weights**: the alpha, beta, gamma, delta weights are tunable and not set. Pick and log them as a decision when implementing.
4. **Play capture method**: bookmarklet, browser extension, desktop wrapper, or mobile. `docs/api-integration/spotify.md` recommends starting with a bookmarklet.
