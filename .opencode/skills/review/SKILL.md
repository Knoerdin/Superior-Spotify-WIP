---
name: review
description: Pre-landing PR review. CRITICAL pass first (data loss, trust-boundary bypass, uncapped spend are forced CRITICAL), then INFORMATIONAL. Detects gh/glab/git-native automatically. Dormant in the planning phase; active from Phase 3.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "false"
---

# Review

## When to invoke
"Review my changes / review this PR / can this land?" — once code exists (Phase 3 onward).

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "review"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **Step 0 detection**: choose the diff source — `gh` PR, `glab` MR, or git-native branch diff.
2. **CRITICAL pass first**: "Data loss, a trust-boundary bypass or uncapped spend is forced CRITICAL" — anything else is ranked below these. Also run **Gate Integrity**: verify the checks that gate the change are real, not bypassed or weakened.
3. **INFORMATIONAL pass**: readability, seams, tests, docs.
4. **Search before recommending** any non-obvious fix.
5. **Report**: findings by severity, then a one-line verdict (ship / ship-with-fixes / hold).

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "review" --outcome <status>`
