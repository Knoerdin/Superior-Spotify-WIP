#!/usr/bin/env bash
# Closes the skill's timeline entry and rewrites .last-status.env with the outcome.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.opencode/state"
mkdir -p "$STATE" 2>/dev/null || true

SKILL="" OUTCOME="" SESSION_ID="${SS_SESSION_ID:-}" TEL_START=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill) SKILL="$2"; shift 2 ;;
    --outcome) OUTCOME="$2"; shift 2 ;;
    --session-id) SESSION_ID="$2"; shift 2 ;;
    --tel-start) TEL_START="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "$SKILL" || -z "$OUTCOME" ]]; then
  echo "SKILL_END_ERROR: need --skill <name> --outcome <DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT>"
  exit 0
fi
case "$OUTCOME" in
  DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT) ;;
  *) echo "SKILL_END_ERROR: outcome must be one of DONE|DONE_WITH_CONCERNS|BLOCKED|NEEDS_CONTEXT"; exit 0 ;;
esac
SLUG="$(printf '%s' "$SKILL" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9.-' '-' | sed -e 's/^-*//' -e 's/-*$//' -e 's/--*/-/g')"

SS_STATE="$STATE" SS_SID="$SESSION_ID" SS_SKILL="$SLUG" SS_OUTCOME="$OUTCOME" SS_TEL="$TEL_START" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE, SS_SID, SS_SKILL, SS_OUTCOME, SS_TEL } = process.env
const rec = { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), session_id: SS_SID || "(unknown)", skill: SS_SKILL, kind: "end", outcome: SS_OUTCOME, at: new Date().toISOString() }
if (SS_TEL) rec.tel_start = SS_TEL
try { fs.appendFileSync(SS_STATE + "/timeline.jsonl", JSON.stringify(rec) + "\n", { encoding: "utf8", flag: "a" }) } catch {}
NODE

cat > "$STATE/.last-status.env" <<ENV
# written by skill-end.sh; do not edit by hand
SESSION_ID=$SESSION_ID
SKILL=$SLUG
OUTCOME=$OUTCOME
ENDED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ENV
echo "SKILL_END_OK: 1"
echo "OUTCOME: $OUTCOME"
