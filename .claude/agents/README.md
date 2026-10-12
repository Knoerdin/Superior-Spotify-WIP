# Superior Spotify - Agent System

This directory contains configuration files for the multi-agent system used in the Superior Spotify project.

## Agent Structure

### Primary Contact
- **orchestrator** - Your direct interface point. Routes tasks to specialized agents.

### Core Implementation Agents (Direct Write)
- **frontend-design** - UI/UX, dashboard, visualizations
- **backend-server** - FastAPI, PostgreSQL, Redis
- **ml-features** - ML algorithms, recommendations, clustering

### Support Agents (Proposal Only)
- **backend-debug** - Error diagnosis and troubleshooting
- **testing-qa** - Test coverage and QA
- **security** - Security review and hardening
- **devops** - Infrastructure and deployment
- **documentation** - Technical documentation
- **data-analytics** - Listening pattern analysis
- **mobile-pwa** - Progressive web app features
- **api-integration** - Spotify API specialist

## How to Use

### Direct Agent Invocation
In Claude Code, you can directly invoke agents by name:
```
/agent frontend-design "Design the dashboard layout"
```

### Using Orchestrator (Recommended)
For most tasks, start with the orchestrator:
```
/agent orchestrator "I want to implement smart shuffle"
```

The orchestrator will:
1. Understand your goal
2. Route to appropriate agents
3. Aggregate results
4. Present synthesized solution

## Agent Files

Each agent has a `.md` file containing:
- Role definition
- Capabilities list
- Permission level
- Project context references
- Decision guidelines
- Collaboration notes

## Shared Context

See `CONTEXT.md` for project-wide information accessible to all agents.

## Task Routing Quick Reference

| Request Type | Agent |
|-------------|-------|
| "Design the dashboard" | frontend-design |
| "Set up database schema" | backend-server |
| "Implement smart shuffle" | ml-features |
| "Debug this OAuth error" | backend-debug |
| "Add tests for X" | testing-qa |
| "Review security of X" | security |
| "Set up deployment" | devops |
| "Update documentation" | documentation |
| "Analyze listening patterns" | data-analytics |
| "Make it mobile-friendly" | mobile-pwa |
| "Fix Spotify API rate limiting" | api-integration |