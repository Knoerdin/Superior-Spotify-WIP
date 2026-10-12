# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## Agent Workflow

**You only talk to the orchestrator.** All tasks flow through it - it delegates to specialized agents.

| Agent | Purpose |
|-------|---------|
| orchestrator | Routes tasks, coordinates all agents |
| frontend-design | UI, dashboards, visualizations |
| backend-server | API, database, Redis |
| ml-features | Algorithms, recommendations |
| backend-debug | Error diagnosis, performance |
| testing-qa | Unit tests, integration tests |
| security | OAuth, authentication |
| devops | Docker, deployment |
| documentation | README, API docs |
| data-analytics | Listening insights |
| mobile-pwa | Mobile, PWA |
| api-integration | Spotify API handling |

**Key rules:**
1. Never let user talk to agents directly
2. Fire agents in parallel for speed
3. Synthesize results before responding to user

See `.claude/WORKFLOW.md` for full workflow details.

---

## Project Status

**Early Concept Phase** - Planning documents exist, implementation not started.

## Current Artifacts

- `Sketches/Home Screen sketch.jpg` - Visual mockup of home screen UI
- `planning/` - Full planning documents

## Planning References

| File | Content |
|------|---------|
| `planning/comprehensive-plan.md` | Full product plan: ML architecture, database schema, feature specs, tech stack, 14-week development roadmap |
| `planning/architecture.md` | High-level system architecture, Spotify API considerations, open questions |
| `planning/tech-stack.md` | Technology recommendations with rationale (Python-centric approach) |
| `planning/project-structure.md` | Directory layout with starter code templates |

---

## Core Problems to Solve

1. **Better Shuffle**: Spotify's shuffle doesn't respect user preferences for variety, mood, context
2. **Pattern-Based Playlists**: Auto-generate playlists based on listening patterns
3. **Deep Statistics**: Track and visualize listening habits beyond what Spotify provides
4. **Social Features**: Share stats, compete with friends

## Technology Stack

| Component | Choice |
|-----------|--------|
| Backend | Python (FastAPI) |
| Database | PostgreSQL |
| Cache | Redis |
| ML | scikit-learn, pandas, numpy |
| Frontend | Next.js or Nuxt + Plotly |
| Deployment | Railway/Render + Vercel |

## Key Spotify API Endpoints

- `/me` - User profile
- `/me/top/{type}` - Top artists/tracks
- `/me/player/recently-played` - Limited history (20-50 tracks)
- `/audio-features/{id}` - Track audio features
- `/recommendations` - Track recommendations

**Critical limitation**: Spotify only gives 20-50 recently played tracks. You must self-track every play event.

## Audio Features (for ML)

Spotify provides these per track (normalized 0-1):
- danceability, energy, valence
- acousticness, instrumentalness, liveness
- speechiness, tempo, loudness, mode, key

## Database Core Tables

- `users` - User profiles and OAuth tokens
- `listening_events` - Self-tracked play history (critical!)
- `tracks` - Track metadata
- `audio_features` - Spotify audio features per track
- `listening_sessions` - Grouped plays by context
- `user_preferences` - Explicit preference weights
- `playlists` - User and system-generated playlists

---

## Next Steps

1. Set up project repository with basic structure
2. Implement OAuth flow with Spotify
3. Create initial database schema
4. Build MVP listening event capture
