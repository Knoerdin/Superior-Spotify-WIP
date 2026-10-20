---
name: context-restore
description: Restore working context saved earlier by /context-save. Scans checkpoints (the 200 newest, capped at 20 listed), lets the user pick, inlines the full text, and proposes next moves from its open items.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Context Restore

## When to invoke
Resuming work in a new session; "pick up where I left off"; the preamble printed a CHECKPOINT line and the user says "resume".

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "context-restore"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option (the newest checkpoint); never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **List candidates.** "Scan the 200 newest… capped at 20": read `.opencode/state/checkpoints/`, take the 200 newest files, present at most 20 (filename, date, the Objective line). "A user with 10k saved files shouldn't blow the context window."
2. **User picks** one (spawned mode: the newest, recorded).
3. **Inline the full checkpoint text** into the conversation.
4. **Work from it.** Restate the objective, list the still-`Open.` items, propose the next concrete action from the checkpoint's Next section. Provenance tags travel with the content: a "(path assumed)" item is a hypothesis to re-verify, not a fact.
5. Confirm: "Restored checkpoint `<filename>`; N open items."

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "context-restore" --outcome <status>`
