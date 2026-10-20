# CLAUDE.md

This file provides guidance for Claude Code when working in this repository.

**Project stage: Early Concept Phase.** Planning documents exist. Implementation has not started.

## Agent Workflow

The **main session is the orchestrator**. It routes work to specialist agents (via the `subagent` tool) and synthesizes their results before answering the user. There is no separate orchestrator agent.

| Agent | Role |
|---|---|
| frontend-design | UI, dashboards, Plotly visualizations (writes `frontend/**`) |
| backend-server | FastAPI, PostgreSQL, Redis, migrations (writes `app/**`, `migrations/**`, `utils/**`) |
| ml-features | Smart shuffle, similarity, clustering, recommendations (writes `ml/**`) |
| backend-debug | Error diagnosis, performance (proposal only) |
| testing-qa | pytest design, coverage (proposal only) |
| security | OAuth security, OWASP, least privilege (proposal only) |
| devops | Docker, Railway/Render, monitoring (proposal only) |
| data-analytics | Listening insights, pandas/scipy (proposal only) |
| mobile-pwa | PWA, mobile optimization (proposal only) |
| api-integration | Spotify API: rate limits, caching, webhooks (proposal only) |
| documentation | README, API docs, ADRs (proposal only) |

Key rules:

1. AI models recommend. Users decide. Never decide scope for the user.
2. Proposal-only agents end their reply with a `## RESULT` section. The main session applies proposals only after user approval.
3. Never start implementation without a plan. A spec or a completed plan review must exist first.
4. Full rules, skill routing, decision log, and safety policy: see `AGENTS.md`.

Legacy note: `.claude/WORKFLOW.md` and `.claude/agents/README.md` describe the old "you only talk to the orchestrator" workflow. `AGENTS.md` supersedes both.

## Current State

- `planning/` contains the full planning set. `docs/` contains four deep-dive documents.
- `Sketches/Home Screen sketch.jpg` is the only UI artifact.
- `frontend/` and `tests/` are empty placeholder directories.
- No backend code, no `requirements.txt`, no `docker-compose.yml`, no `.env.example`, no `migrations/`.
- `AGENTS.md` and `.opencode/` are the OpenCode port (committed; per-machine state in `.opencode/state/` is gitignored).

## Planning References

| File | Content |
|---|---|
| `planning/comprehensive-plan.md` | Full product plan: ML architecture, database schema, feature specs, 14-week roadmap |
| `planning/architecture.md` | High-level system architecture, Spotify API considerations, open questions |
| `planning/tech-stack.md` | Technology options with rationale (Python-centric) |
| `planning/project-structure.md` | Directory layout with starter code templates |

## Core Problems to Solve

1. **Better Shuffle**: Spotify's shuffle does not respect user preferences for variety, mood, or context
2. **Pattern-Based Playlists**: Auto-generate playlists from listening patterns
3. **Deep Statistics**: Track and visualize listening habits beyond what Spotify provides
4. **Social Features**: Share stats, compare taste with friends

## Technology Stack

| Component | Choice |
|---|---|
| Backend | Python (FastAPI) |
| Database | PostgreSQL |
| Cache | Redis |
| ML | scikit-learn, pandas, numpy |
| Frontend | Open decision: HTMX/Jinja2, Next.js, or Nuxt (see `planning/tech-stack.md` and the note in `AGENTS.md`) |
| Deployment | Railway/Render + Vercel |

## Key Spotify API Endpoints

- `/me` - User profile
- `/me/top/{type}` - Top artists/tracks
- `/me/player/recently-played` - Limited history (20 to 50 tracks)
- `/audio-features/{id}` - Track audio features
- `/recommendations` - Track recommendations

The hard limitation: Spotify returns only 20 to 50 recently played tracks. Every play event must be self-tracked into `listening_events`.

## Audio Features (for ML)

12 features per track, the union used in this project:

- danceability, energy, valence
- acousticness, instrumentalness, liveness
- speechiness, tempo, loudness
- mode, key, time_signature

The first seven are normalized 0 to 1. tempo and loudness are not normalized. mode and key need scaling before similarity math.

## Database Core Tables

8 core tables, the union used in this project:

- `users` - User profiles and OAuth tokens
- `listening_events` - Self-tracked play history
- `tracks` - Track metadata
- `audio_features` - Spotify audio features per track
- `listening_sessions` - Grouped plays by context
- `user_preferences` - Explicit preference weights
- `playlists` - User and system-generated playlists
- `friend_connections` - Social graph

**Open item**: `CLAUDE.md` historically listed 7 tables and 11 features; `.claude/agents/CONTEXT.md` lists 8 and 12. This file uses the union per `AGENTS.md`. Lock the counts in `/spec` before schema work. `.claude/agents/CONTEXT.md` is the source of truth for the union list.

## Next Steps

1. Run `/spec` to lock open decisions: frontend choice, schema counts (8/12), smart shuffle weights, play capture method
2. Phase 3 (per `AGENTS.md`): scaffold `app/` structure and implement the Spotify OAuth flow
3. Phase 3: create the initial database schema, then MVP listening event capture
4. Phase 4: implement `ml/` components (smart shuffle first, per `docs/ml/smart-shuffle.md`)
