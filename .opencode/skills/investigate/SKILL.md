---
name: investigate
description: Systematic debugging with root cause investigation. Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST. Pattern table, 3-strike limit, DEBUG REPORT. Dormant in the planning phase; active from Phase 3.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

# Investigate

## When to invoke
"Something is broken / why does X / this bug" — once code exists (Phase 3 onward).

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "investigate"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

**Iron Law: NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.**

1. **Reproduce.** A failing command, test, or minimal repro — before any hypothesis.
2. **Match the pattern table** before hypothesizing: race / nil / state-corruption / integration / config-drift / stale-cache. Note: "recurring bugs in the same files are an architectural smell" — two bugs in one file is a signal, not a coincidence.
3. **Hypothesize with evidence.** Each hypothesis names the evidence that would confirm or kill it.
4. **Fix and verify.** "Quick fix for now — there is no 'for now.'" — banned; "Never say 'this should fix it.'" — banned. The fix is verified by the repro passing.
5. **3-strike rule.** After 3 failed fix attempts: stop, report what was tried and what evidence remains, and ask.

**Blast radius:** if the fix will touch more than 5 files, ask the user before proceeding.

End with a **DEBUG REPORT** box: symptom → root cause (with evidence) → fix → verification → regression test (if any).

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "investigate" --outcome <status>`
