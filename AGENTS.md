# AGENTS.md — Superior Spotify

## Project

A "nerdy" Spotify-enhanced web app: ML-powered smart shuffle, pattern-based playlists, deep listening statistics, and social features. **Early Concept Phase — planning documents exist, implementation not started.**

- Full plan: `planning/comprehensive-plan.md` (14-week roadmap). Architecture: `planning/architecture.md`. Stack: `planning/tech-stack.md`. Layout: `planning/project-structure.md`.
- Deep docs: `docs/ml/smart-shuffle.md`, `docs/backend/foundation.md`, `docs/api-integration/spotify.md`, `docs/security/oauth.md`. UI mockup: `Sketches/Home Screen sketch.jpg`.
- Stack: FastAPI + PostgreSQL + Redis + scikit-learn/pandas/numpy; frontend Next.js or Nuxt + Plotly (not yet chosen); deploy Railway/Render + Vercel.
- Smart shuffle scores tracks as α·play_frequency + β·audio_similarity + γ·diversity_bonus − δ·recency_penalty; "Tunable weights (start with balanced values)" — do not invent exact values; pick and log them as a decision when implementing.

**Docs discrepancy (resolve in /spec before schema work):** CLAUDE.md lists 7 core tables and 11 audio features; `.claude/agents/CONTEXT.md` lists 8 (adds `friend_connections`) and 12 (adds `time_signature`). This file uses the union (8 tables, 12 features). Also: the stack table says Next.js/Nuxt but `project-structure.md` lists Streamlit as rapid-MVP frontend — decide the frontend strategy explicitly.

## How to work

1. **AI models recommend. Users decide.** That rule overrides all others. Never decide scope for the user; present options with a recommendation and wait.
2. **Never auto-choose a destructive or irreversible option.** Take the conservative non-destructive choice and record what you chose and why.
3. Search before recommending: "has someone already solved this?" before building.
4. No self-certification: verify claims with evidence (a run, a read, a test) before reporting them as true.
5. Do the complete thing. Every time. No half-phases left dangling without saying so.
6. Voice: no em dashes. No AI vocabulary: delve, crucial, robust, comprehensive, nuanced, multifaceted, load-bearing.
7. Stuck after 3 attempts on the same problem: stop, report what was tried, ask.

## Team

The main session IS the orchestrator: it routes work to specialist agents (via the `subagent` tool) and synthesizes their results before answering the user. There is no separate orchestrator agent.

| Agent | Role | Write scope | Phase |
|---|---|---|---|
| frontend-design | UI, dashboards, Plotly visualizations | `frontend/**` | 3 |
| backend-server | FastAPI, PostgreSQL, Redis, migrations | `app/**`, `migrations/**`, `utils/**` | 3 |
| ml-features | smart shuffle, similarity, clustering, recommendations | `ml/**` | 4 |
| backend-debug | error diagnosis, performance (root cause first) | none (proposal only) | 2 |
| testing-qa | pytest design, coverage | none (proposal only) | 2 |
| security | OAuth security, OWASP, least privilege | none (proposal only) | 2 |
| devops | Docker, Railway/Render, monitoring | none (proposal only) | 2 |
| data-analytics | listening insights, pandas/scipy | none (proposal only) | 2 |
| mobile-pwa | PWA, mobile optimization | none (proposal only) | 2 |
| api-integration | Spotify API: rate limits, caching, webhooks | none (proposal only) | 2 |
| documentation | README, API docs, ADRs | none (proposal only) | 4 |

Proposal-only agents end their reply with a `## RESULT` section: what they propose, files touched (or "none"), decisions to log, suggested next step. The main session applies proposals only after the user approves.

**Spawned agent contract:** subagents never ask the user questions (the `question` tool is denied for them by frontmatter). When a decision is needed, auto-choose the recommended option, never a destructive one, and record the choice under "Decisions to log" in the result.

## Skill routing

| Intent | Skill |
|---|---|
| "I have an idea / what should I build / help me think" | `/office-hours` |
| "write a spec / make this precise" | `/spec` |
| "is this plan worth it / challenge my plan" | `/plan-ceo-review` |
| "review this plan technically" | `/plan-eng-review` |
| "something is broken / bug / why does X" | `/investigate` |
| "review my changes / PR review" | `/review` |
| "test this / QA" | `/qa` |
| "ship it / release / push" | `/ship` |
| "save context / checkpoint" | `/context-save` |
| "resume / pick up where I left off" | `/context-restore` |
| "what did we learn / learnings" | `/learn` |

Skills load by exact ID with the `skill` tool (or an `@skill-id` mention); `/name` works in the TUI when exposed. If the intent is unclear, start with `/office-hours`. **Never start implementation without a plan** — a spec or a completed plan review must exist first.

## Decision log

- Log DURABLE decisions with `.opencode/scripts/decision-log.sh`: architecture, scope, tool/vendor choice, any reversal. Not trivial or turn-level choices.
- Before working, read active decisions (the preamble prints them). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals.
- Reversals are logged with `--supersede`, not deleted.

## Learnings

At the end of every skill session: a 5+ minute review. Anything that "would save 5+ minutes in a future session" is logged via `.opencode/scripts/learnings-log.sh`. A valid outcome is the explicit line "No durable learnings this session."

## Checkpoints

- Save before risky steps with `/context-save` (items carry provenance tags; every item starts `Open.`).
- At session start, the preamble surfaces the latest checkpoint; `/context-restore` lists candidates (scan the 200 newest, capped at 20).
- V2 per-step snapshots (`/undo` / `/redo`) and auto-compaction are additional safety nets, not replacements for checkpoints.

## Safety

- `.env` is never read or committed (OpenCode denies `.env` reads by rule; `.gitignore` covers it).
- Destructive operations (force push, history rewrite, dropping data, deleting files) require explicit user confirmation, every time.
- Never ship from `main`; work on feature branches.
- Spotify OAuth secrets live in `.env` only; never in code, logs, or committed files.

## Completion status

Every skill session ends with exactly one status:
- **DONE** — the work is complete and verified.
- **DONE_WITH_CONCERNS** — complete, but with listed caveats.
- **BLOCKED** — cannot proceed; names the blocker.
- **NEEDS_CONTEXT** — needs information only the user has.
