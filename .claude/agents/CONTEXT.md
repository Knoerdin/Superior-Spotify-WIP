# Superior Spotify - Agent Context

This file contains shared context for all agents working on the Superior Spotify project.

## Project Overview

**Vision**: A "nerdy" Spotify-enhanced web app that brings ML capabilities, deep statistics, and social features to Spotify.

**Core Problems**:
1. Better shuffle that respects user preferences for variety, mood, and context
2. Pattern-based playlist generation
3. Deep listening statistics and visualization
4. Social features for music taste comparison

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | FastAPI (Python) |
| Database | PostgreSQL |
| Cache | Redis |
| ML | scikit-learn, pandas, numpy |
| Frontend | Next.js/Nuxt with Plotly |
| Deployment | Railway/Render + Vercel |

## Key References

- [Spotify Web API Docs](https://developer.spotify.com/documentation/web-api)
- Project planning: `../../planning/comprehensive-plan.md`
- Architecture: `../../planning/architecture.md`
- Tech stack: `../../planning/tech-stack.md`
- Project structure: `../../planning/project-structure.md`

## Database Core Tables

- `users` - User profiles and OAuth tokens
- `listening_events` - Self-tracked play history (critical!)
- `tracks` - Track metadata
- `audio_features` - Spotify audio features per track
- `listening_sessions` - Grouped plays by context
- `user_preferences` - Explicit preference weights
- `playlists` - User and system-generated playlists
- `friend_connections` - Social graph

## Audio Features (for ML)

Spotify provides these per track (normalized 0-1):
- danceability, energy, valence, acousticness
- instrumentalness, liveness, speechiness
- tempo, loudness, mode, key, time_signature

## Project Stage

**Early Concept Phase** - Planning documents exist, implementation not started.

## Agent Permission Levels

| Agent Type | Permission |
|------------|------------|
| Frontend Design | Direct Write |
| Backend Server | Direct Write |
| ML Features | Direct Write |
| Orchestrator | Proposal Only |
| Backend Debug | Proposal Only |
| Testing/QA | Proposal Only |
| Security | Proposal Only |
| DevOps | Proposal Only |
| Documentation | Proposal Only |
| Data Analytics | Proposal Only |
| Mobile/PWA | Proposal Only |
| API Integration | Proposal Only |
