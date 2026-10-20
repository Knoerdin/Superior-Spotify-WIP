---
name: spec
description: Turn vague intent into a precise, executable spec in five phases (why, scope, technical with mandatory code-reading, draft, file). Use when the user wants a design doc or idea made precise before implementation. Blocks below 7/10 confidence.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Spec

## When to invoke
After `/office-hours`, or whenever the user says "make this precise / write a spec / what exactly are we building".

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "spec"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **Flag Reference.** Open with the list of open flags (unresolved questions) and keep it current as phases resolve them.
2. **Five phases: why, scope, technical, draft, file.** "Do NOT proceed until all five are answered without hand-waving." A phase that is not fully answered stays open in the Flag Reference.
3. **Technical phase: read before you write.** "read at least one piece of evidence… This is the magical moment for the user" — show the user what you actually read (planning docs, existing code, the Spotify API docs), not a guess.
4. **Draft.** Write the spec (requirements, scope in/out, data model, interfaces, acceptance criteria). Quality gate: any section below 7/10 confidence is blocked and re-asked, not shipped.
5. **Verification.** Ask the user: "Does this accurately capture what you want? What did I get wrong?" Iterate until they confirm.
6. **File.** Save the spec (markdown) under `planning/` or `docs/` and name it in the completion report.

**How to ask questions** (applies to every phase): one question at a time; concrete, not hypothetical; offer options with a recommendation; wait for the answer before moving on; no compound questions; stop asking when the answer is in.

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "spec" --outcome <status>`
