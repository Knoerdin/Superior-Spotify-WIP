---
name: context-save
description: Save working context. Use before risky steps (migrations, deploys, large refactors), on user request, or before the session compacts. Writes a provenance-tagged checkpoint markdown file.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Context Save

## When to invoke
Before anything risky or long-running; when the user says "save context / checkpoint"; at the end of a productive session.

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "context-save"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

Write one markdown file to `.opencode/state/checkpoints/YYYYMMDDTHHMMSSZ-<slug>.md` with this shape:

```
# Checkpoint — <slug>
PROJECT: Superior Spotify
DATE: <utc iso>
SESSION_ID: <from preamble>
SKILL: <current skill>

## Objective
<one or two lines>

## State
- <claim> (target state checked)
- <claim> (code read)
- <claim> (path assumed)

## Actions
- <thing done> (path run)
- <thing done> (path read)
- <thing done> (path assumed)

## Open items
- [ ] <item> — Open.
- [ ] <item> — Open.

## Next
- <concrete next step>
```

Rules: every State/Actions item carries a provenance tag — claims "(target state checked)|(code read)|(path assumed)"; actions "(path run)|(path read)|(path assumed)". "Every item starts with the status `Open.`" until closed. Foreign checkpoints (saved by another session or machine) are reported, not adopted (SHARED_BUCKET rule). Then confirm to the user in one line: "Checkpoint saved: `<filename>`".

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "context-save" --outcome <status>`
