---
name: plan-ceo-review
description: CEO/founder-mode plan review. Challenges premises, builds the dream state, scores alternatives, selects scope mode (EXPANSION/SELECTIVE/REDUCTION/HOLD), runs the 10x check. Read-only: ends with a report the machine can verify.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Plan CEO Review

## When to invoke
"When is this plan worth it / too big / too small", or after a spec exists and before implementation.

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "plan-ceo-review"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow (read-only — never implement in this skill)

- **0A Premise Challenge.** Is the premise worth pursuing? Argue the strongest case against the plan and see if the plan survives it.
- **0C Dream State.** Three horizons: CURRENT state → what this plan changes → 12-MONTH state. If the plan is not a step on the line from current to 12-month, say so.
- **0D Alternatives.** At least two real alternatives to the chosen approach, each scored on coverage 10/7/3 (full coverage / partial / gap).
- **0E Mode selection.** "Go big" from the user → EXPANSION; "cherry-pick" → SELECTIVE; more than 15 planned changed files → REDUCTION; greenfield project → EXPANSION; adding a capability to an existing surface → SELECTIVE; fixing or refactoring → HOLD. Name the selected mode explicitly.
- **0G 10x check.** If the budget were 10x, what would be different? The Platonic ideal of this feature, plus a 5×30-minute delight scan (five small delights, each ≤30 minutes).

## Report gate (the machine check)

End the skill with a report whose LAST `## ` heading is exactly `## GSTACK REVIEW REPORT`, containing a one-line VERDICT. The final line of the skill output must be exactly `NO UNRESOLVED DECISIONS` (unbolded). If any decision is unresolved, list them under `## OPEN DECISIONS` instead — the sentinel must not appear while anything is open.

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "plan-ceo-review" --outcome <status>`
