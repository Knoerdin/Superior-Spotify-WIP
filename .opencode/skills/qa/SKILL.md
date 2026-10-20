---
name: qa
description: Fix browser/API/CLI/job/worker/webhook bugs. Tiers Quick/Standard/Exhaustive, clean-tree gate, timestamped run reports, and a fix loop that writes one regression test per fixed bug. Dormant in the planning phase; active from Phase 3.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

# QA

## When to invoke
"Test this / QA / does this actually work?" — once runnable code exists (Phase 3 onward). In this project: API-level tests first (no browser runtime is ported).

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "qa"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **Setup params**: scope (what surface), tier (Quick / Standard / Exhaustive), and the evidence bar per tier.
2. **Clean-tree gate — STOP:** if the working tree is dirty, stop and offer the user: commit, stash, or abort. Do not run QA on a dirty tree.
3. **Run** the tests/flows for the tier; failures are captured with output, not paraphrased.
4. **Run report**: write `.opencode/state/qa/run-YYYYMMDDTHHMMSSZ-<slug>.md` (setup, matrix, results, failures with evidence).
5. **Fix loop (per failure)**: 8a reproduce + value card (what is broken, why it matters) → 8a.5 confirm the card with the user (spawned: auto-choose the conservative path and record) → 8b minimal fix → 8c re-test. One regression test per fixed bug, named `{name}.regression-N.test.{ext}` (here: `{name}.regression-N.test.py`).

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "qa" --outcome <status>`
