# Superior Spotify

A "nerdy" Spotify-enhanced web app that brings ML capabilities, deep statistics, and social features to your music listening experience.

## Vision

Spotify's default shuffle and recommendations don't always respect your personal preferences, mood, or listening context. Superior Spotify fills that gap with:

- **Smart Shuffle**: Weighted random based on your listening frequency + audio preferences
- **Pattern-Based Playlists**: Auto-generate playlists based on time of day, mood, listening habits
- **Deep Statistics**: Track and visualize listening habits beyond what Spotify provides
- **Social Features**: Share stats, compete with friends, discover through social connections

## Project Status

**Early Concept Phase** - This repository contains planning documents and agent configurations. Implementation has not yet started.

## Multi-Agent Development System

This project uses a specialized multi-agent system for development. Each agent handles specific aspects:

### Core Agents (Direct Write Access)

| Agent | Purpose |
|-------|---------|
| `frontend-design` | UI/UX, dashboard visualizations, responsive design |
| `backend-server` | FastAPI backend, PostgreSQL database, Redis caching |
| `ml-features` | ML algorithms, audio similarity, smart shuffle, clustering |

### Support Agents (Proposal Mode)

| Agent | Purpose |
|-------|---------|
| `orchestrator` | Primary contact point, coordinates all agents |
| `backend-debug` | Error diagnosis, performance troubleshooting |
| `testing-qa` | Unit tests, integration tests, CI/CD |
| `security` | OAuth security, API authentication, data privacy |
| `devops` | Docker, deployment (Railway/Render), monitoring |
| `documentation` | README, API docs, architectural decisions |
| `data-analytics` | Listening pattern analysis, insights |
| `mobile-pwa` | Progressive web app, mobile optimization |
| `api-integration` | Spotify API specialist, rate limiting, caching |

### How to Use the Agent System

For most tasks, start with the **orchestrator** agent - it routes work to the appropriate specialist:

```
/agent orchestrator "I want to implement smart shuffle"
```

The orchestrator will delegate to `ml-features` and `backend-server` as needed.

See `.claude/agents/README.md` for detailed agent documentation.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| ML | scikit-learn, pandas, numpy |
| Frontend | Next.js/Nuxt with Plotly |
| Deployment | Railway/Render + Vercel |

## Quick Start (When Implementation Begins)

```bash
# 1. Set up virtual environment
python -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start PostgreSQL (Docker)
docker run --name spotify-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres

# 4. Run backend
uvicorn app.main:app --reload

# 5. Open browser
# http://localhost:8000
```

## Project Documentation

- **Full Product Plan**: `planning/comprehensive-plan.md`
- **Architecture Overview**: `planning/architecture.md`
- **Tech Stack Details**: `planning/tech-stack.md`
- **Project Structure**: `planning/project-structure.md`

## References

- [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api)
