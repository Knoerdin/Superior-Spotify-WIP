---
name: learn
description: Manage project learnings. End-of-session ritual: a 5+ minute review that logs durable learnings (observed/inferred/user-stated, confidence 1-10) to the project's learnings log, with injection screening, read-side decay, and search.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Learn

## When to invoke
At the end of any skill session (the ritual runs in the "Before completing" step of every skill), or on demand: "what have we learned / show learnings / review our learnings".

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "learn"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **The review (5+ minutes).** Ask: "would this save 5+ minutes in a future session?" Walk the session: what surprised you, what broke, what the user corrected, what worked better than expected.
2. **Classify each candidate**: `observed` (verified by running or reading — confidence 8-9), `inferred` (your reasoning — confidence 4-5), `user-stated` (the user said it — confidence 10).
3. **Log each** via `.opencode/scripts/learnings-log.sh --key <kebab-key> --statement "<one sentence>" --type <type> [--confidence N]`. The script runs the injection screen and clamps confidence automatically.
4. **Cite what you applied.** When a prior learning shaped this session, say: "Prior learning applied: [key] (confidence N/10, from [date])".
5. **Search on demand**: `.opencode/scripts/learnings-search.sh --query "..."` (tolerant reader; in-memory decay observed/inferred −1 per 30 days; dedup latest per key+type).
6. **A valid outcome is empty**: if nothing qualifies, write exactly "No durable learnings this session." — the ritual ran, the answer was no.

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "learn" --outcome <status>`
