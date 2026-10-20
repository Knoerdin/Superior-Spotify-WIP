---
name: ship
description: Ship workflow: pre-flight (never from the base branch), merge base BEFORE tests, bisectable commits, verification gate, push. Dormant in the planning phase; active from Phase 3.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

# Ship

## When to invoke
"Ship it / release / push this" — once code exists and review is clean (Phase 3 onward).

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "ship"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **Pre-flight (Step 1).** "You're on the base branch. Ship from a feature branch." — if on `main`, STOP: create the feature branch or ask. In this project: work on a feature branch off `main`, never commit directly to `main`.
2. **Merge base FIRST.** Compute the merge base before running tests, so the test run covers exactly what will be shipped.
3. **Bisectable chunks.** Commits as one-concern chunks; a reviewer can bisect the branch cleanly.
4. **Verification Gate.** All tests green, review clean, no dirty-tree surprises — before any push.
5. **Push** the branch (spawned: record, never force-push). Merging to `main` and any deploy require explicit user approval, every time.

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "ship" --outcome <status>`
