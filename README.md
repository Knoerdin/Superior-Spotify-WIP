# Superior Spotify

A "nerdy" Spotify-enhanced web app. ML-powered smart shuffle, pattern-based playlists, deep listening statistics, and social features.

Repo: https://github.com/Knoerdin/Superior-Spotify-WIP

## Project Status

**Planning phase. No implementation exists.**

- This repository contains planning documents, deep docs, agent configs, and one UI mockup.
- `frontend/` and `tests/` are empty placeholder directories.
- There is no `app/`, no `requirements.txt`, no `docker-compose.yml`, no `.env.example`, no `migrations/`.
- A short-lived backend was removed in commit `a360959` ("Remove backend files").
- The plan of record for when implementation starts: the 14-week roadmap in `planning/comprehensive-plan.md`.

## Features

Spotify's default shuffle and recommendations do not respect personal preferences for variety, mood, or context. Superior Spotify fills that gap:

| Feature | What it does |
|---|---|
| **Smart Shuffle** | Weighted shuffle from your listening frequency plus audio feature preferences |
| **Pattern Playlists** | Auto-generated playlists by time of day, mood, and habits |
| **Deep Statistics** | Track and visualize listening habits beyond what Spotify shows |
| **Social** | Compare taste, share stats, connect with friends |

One hard constraint shapes all of this: the Spotify API returns only 20 to 50 recently played tracks. The app must self-track every play event into its own database. See `docs/api-integration/spotify.md`.

## Repository Layout

What exists today:

```
.
├── AGENTS.md            # Agent orchestration rules (source of truth for how work happens)
├── CLAUDE.md            # Project context for Claude Code sessions
├── QUICKSTART.md        # What exists today, and what to expect next
├── planning/
│   ├── comprehensive-plan.md    # Full product plan, ML architecture, 14-week roadmap
│   ├── architecture.md          # High-level architecture, data flow, open questions
│   ├── tech-stack.md            # Stack options and rationale (Python-centric)
│   └── project-structure.md     # Intended directory layout, starter templates
├── docs/
│   ├── ml/smart-shuffle.md      # Smart shuffle algorithm spec
│   ├── backend/foundation.md    # FastAPI, SQLAlchemy, Redis guidance
│   ├── api-integration/spotify.md  # API limits, caching, self-tracking design
│   └── security/oauth.md        # OAuth, tokens, JWT, privacy
├── Sketches/Home Screen sketch.jpg  # Home screen UI mockup
├── .claude/               # Claude Code agent configs (legacy harness, kept for now)
└── .opencode/             # OpenCode agents, skills, scripts (per-machine state/ is gitignored)
```

Planned layout when implementation begins: `app/` (FastAPI), `ml/`, `utils/`, `tests/`, `migrations/`, `frontend/`, `scripts/`. See `planning/project-structure.md`.

## Agent System

The **main session is the orchestrator**: it routes work to specialist agents, synthesizes their results, and answers the user. There is no separate orchestrator agent.

Core agents with direct write access:

| Agent | Writes to | Role |
|---|---|---|
| `frontend-design` | `frontend/**` | UI, dashboards, Plotly visualizations |
| `backend-server` | `app/**`, `migrations/**`, `utils/**` | FastAPI, PostgreSQL, Redis, migrations |
| `ml-features` | `ml/**` | Smart shuffle, similarity, clustering, recommendations |

Proposal-only agents (they propose, never write directly): `backend-debug`, `testing-qa`, `security`, `devops`, `data-analytics`, `mobile-pwa`, `api-integration`, `documentation`.

The rules, skill routing, decision log, learnings, checkpoints, and safety policy live in `AGENTS.md`. Read it first.

## Technology Stack

| Component | Choice |
|---|---|
| Backend | Python (FastAPI) |
| Database | PostgreSQL (SQLAlchemy, Alembic) |
| Cache / queue | Redis (Celery for background jobs) |
| ML | scikit-learn, pandas, numpy |
| Charts | Plotly |
| Frontend | **Open decision** (below) |
| Deployment | Railway/Render + Vercel |

**The frontend is an open decision.** The docs disagree:

- `planning/tech-stack.md` recommends Option 1: Python-centric, HTMX + Jinja2 or vanilla JS served by FastAPI.
- `AGENTS.md` and `CLAUDE.md` list Next.js or Nuxt (with Plotly) as the SPA candidate.
- `planning/project-structure.md` lists Streamlit as the rapid-MVP frontend.

Do not pick silently. Resolve in `/spec` before any frontend work.

## Documentation Index

| File | Content |
|---|---|
| `AGENTS.md` | How agents work here: rules, routing, decision log, safety |
| `CLAUDE.md` | Project context for Claude Code sessions |
| `QUICKSTART.md` | Current state, what to expect when implementation begins |
| `planning/comprehensive-plan.md` | Full product plan, DB schema, feature specs, 14-week roadmap |
| `planning/architecture.md` | High-level architecture, data flow, Spotify API considerations |
| `planning/tech-stack.md` | Stack options with rationale |
| `planning/project-structure.md` | Intended layout, starter code templates |
| `docs/ml/smart-shuffle.md` | Shuffle scoring, similarity, MMR, bandits, open questions |
| `docs/backend/foundation.md` | FastAPI structure, SQLAlchemy, indexes, caching, testing |
| `docs/api-integration/spotify.md` | API capabilities and limits, rate limits, caching, self-tracking |
| `docs/security/oauth.md` | OAuth flow, token storage, JWT, GDPR, hardening checklist |
| `.claude/agents/README.md` | Agent system overview (Claude Code harness) |
| `.claude/agents/CONTEXT.md` | Shared agent context: DB tables, audio features, project stage |

## Newcomer Orientation

1. Read `AGENTS.md`. It defines how work happens in this repo.
2. Read `planning/comprehensive-plan.md`. It is the plan of record.
3. Read `docs/api-integration/spotify.md`. Self-tracking is the foundation of the product.
4. Look at `Sketches/Home Screen sketch.jpg` for the intended home screen.
5. Ready to build: run `/spec` to lock the open decisions (frontend, schema counts, capture method).

## References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
