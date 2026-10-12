# Agent Workflow

## How This Works

### You Talk To Orchestrator Only

When you have a task, simply state it. The orchestrator handles the rest.

```
Example: "I want to implement smart shuffle"

What happens:
1. Orchestrator understands your goal
2. Orchestrator fires ml-features + backend-server in parallel
3. Agents do their work
4. Orchestrator synthesizes the results
5. You get a unified answer
```

## Agent Roles at a Glance

| Agent | Does This |
|-------|-----------|
| orchestrator | Routes tasks, coordinates everything |
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

## Key Rules

1. **You never talk to agents directly** - Always through orchestrator
2. **Orchestrator fires agents in parallel** - For speed
3. **Orchestrator synthesizes results** - You get one answer, not 5 separate responses
4. **Direct write agents** (frontend, backend, ml) can modify code
5. **Proposal agents** (orchestrator + others) suggest changes for approval

## When You're Ready

Just say what you want to build. Example:

- "Set up the database schema"
- "Implement smart shuffle algorithm"
- "Design the dashboard layout"

The orchestrator routes it to the right agent(s).
