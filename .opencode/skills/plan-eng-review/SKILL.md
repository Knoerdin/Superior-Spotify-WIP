---
name: plan-eng-review
description: Eng manager-mode plan review. Review the selected target. Do not build features. Scope gate first (hard STOP), then architecture, code quality, tests, performance. Read-only: ends with a report the machine can verify.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Plan Eng Review

## When to invoke
"Review this plan technically" — after the CEO review, before implementation.

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "plan-eng-review"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow (read-only — Review the selected target. Do not build features.)

1. **Scope gate — hard STOP, first.** Choose the review target: "Recommendation: A when a branch diff exists, otherwise B. Reply with A, B, or C. STOP and wait for the answer." (A = branch diff, B = plan/spec doc, C = something else named by the user.)
2. **Section 1 — Architecture.** Does the plan's structure hold? Data flow, boundaries, the Spotify API contract, self-tracked `listening_events` as the source of truth.
3. **Section 2 — Code quality.** Where will the plan produce weak code? Naming, module seams, the starter templates in `planning/project-structure.md`.
4. **Section 3 — Test.** What is untestable in the plan as written? Demand testable seams (the ML scoring must be exercisable without live Spotify calls).
5. **Section 4 — Performance.** Hot paths: shuffle scoring over the full library, feature batch-fetch (max 100/call), cache strategy.

## Report gate
End with the report whose LAST `## ` heading is exactly `## GSTACK REVIEW REPORT`, one-line VERDICT, and final line exactly `NO UNRESOLVED DECISIONS` (unbolded) — or `## OPEN DECISIONS` instead if anything is open.

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "plan-eng-review" --outcome <status>`
