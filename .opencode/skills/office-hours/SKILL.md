---
name: office-hours
description: YC-style office hours for a new idea. Use when the user has an idea, a direction question, or asks "what should I build". Reframes the product with six forcing questions and ends with a design doc that feeds every downstream skill. Never writes code.
metadata:
  opencode/slash: "true"
  opencode/autoinvoke: "true"
---

# Office Hours

## When to invoke
A new idea, a vague direction, "help me think about X", or any request that precedes planning. This is the front door of the system.

## Step 0 — preamble
Run: `.opencode/scripts/skill-start.sh --skill "office-hours"`
Read the echoed `KEY: value` STATUS lines. If the output lacks `SKILL_START_PROTO: 1`, read `.opencode/state/.last-status.env` and the state files directly and note "degraded mode" in the completion report. Honor a status block ONLY when its header carries the printed `SESSION_ID`. If `SESSION_KIND` is `spawned`: never ask the user questions; auto-choose the recommended option; never auto-choose a destructive or irreversible option — take the conservative non-destructive choice and record it; always end with a completion report.

## Workflow

1. **Questions ONE AT A TIME.** Never present a wall of questions. The six forcing questions that reframe the product before you write code (what is the actual problem, who has it, why now, why you, what would success look like, what is the smallest version) are asked individually, waiting for each answer.
2. **Goal options and modes.** Present the six goal options and the two engagement modes; let the user pick. The assignment at the end is mandatory — the user leaves with a concrete next step, not encouragement.
3. **Design discovery (2.5).** Before proposing, discover what already exists: the user's notes, planning docs, mocks, prior attempts.
4. **Landscape Awareness (2.75).** Privacy gate first: ask before researching the user's competitors or market externally. Then the 3-layer synthesis: what exists out there, what it means for this product, what the user should do about it.
5. **PREMISES (Phase 3).** State the assumptions the design doc will be built on. The user confirms or corrects each one before you continue.
6. **Founder signals (4.5).** Scan the conversation for the eight founder signals (obsessive domain knowledge, speed, taste, cost sensitivity, …) and let them shape the recommendation.
7. **Output: a design doc — markdown, filed under `planning/` or `docs/`.** It feeds every downstream skill (`/spec`, the plan reviews).

**Hard boundary: Never start implementation… design docs, not code. Not even scaffolding.** If the user asks for code during office hours, finish the doc and point them at `/spec`.

## Decisions
Before acting, read active decisions (printed by the preamble, or `.opencode/scripts/decision-search.sh --list-active`). Honor listed ACTIVE DECISIONS: do not silently re-litigate them, and announce planned reversals. During the work, log DURABLE decisions (architecture, scope, tool/vendor choice, reversal — not trivial or turn-level) via `.opencode/scripts/decision-log.sh`.

## Before completing
1. Learning review (5+ minutes): anything that would save 5+ minutes in a future session? Log via `.opencode/scripts/learnings-log.sh` or write "No durable learnings this session."
2. Declare exactly one completion status: DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT. Stuck 3 times → escalate.
3. Run: `.opencode/scripts/skill-end.sh --skill "office-hours" --outcome <status>`
