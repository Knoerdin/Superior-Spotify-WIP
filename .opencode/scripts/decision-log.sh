#!/usr/bin/env bash
# Append one durable decision to .opencode/state/decisions.jsonl, then rebuild
# decisions.active.json. Schema (gstack): {decision, scope, source, rationale,
# alternatives_considered, branch, issue, confidence}. --supersede retires a
# prior id (it stays in the JSONL; only the projection drops it).
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.opencode/state"
mkdir -p "$STATE" 2>/dev/null || true

DECISION="" SCOPE="project" SOURCE="user" RATIONALE="" ALTS="" BRANCH="" ISSUE="" CONF="" SUPERSEDE=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --decision) DECISION="$2"; shift 2 ;;
    --scope) SCOPE="$2"; shift 2 ;;
    --source) SOURCE="$2"; shift 2 ;;
    --rationale) RATIONALE="$2"; shift 2 ;;
    --alternative) ALTS="$ALTS${ALTS:+,}$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --issue) ISSUE="$2"; shift 2 ;;
    --confidence) CONF="$2"; shift 2 ;;
    --supersede) SUPERSEDE="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "$DECISION" ]]; then
  echo "DECISION_LOG_ERROR: need --decision"
  exit 0
fi
case "$SCOPE" in project|feature|module) ;; *) echo "DECISION_LOG_ERROR: scope must be project|feature|module"; exit 0 ;; esac

SS_STATE="$STATE" SS_DECISION="$DECISION" SS_SCOPE="$SCOPE" SS_SOURCE="$SOURCE" SS_RATIONALE="$RATIONALE" SS_ALTS="$ALTS" SS_BRANCH="$BRANCH" SS_ISSUE="$ISSUE" SS_CONF="$CONF" SS_SUPERSEDE="$SUPERSEDE" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE, SS_DECISION, SS_SCOPE, SS_SOURCE, SS_RATIONALE, SS_ALTS, SS_BRANCH, SS_ISSUE, SS_CONF, SS_SUPERSEDE } = process.env
const now = new Date().toISOString()
const id = "dec-" + Date.now().toString(36)
const conf = SS_CONF === "" ? 7 : Math.max(1, Math.min(10, Math.round(Number(SS_CONF) || 7)))
const rec = {
  id, decision: SS_DECISION, scope: SS_SCOPE, source: SS_SOURCE,
  rationale: SS_RATIONALE || "",
  alternatives_considered: SS_ALTS ? SS_ALTS.split(",").map((s) => s.trim()).filter(Boolean) : [],
  branch: SS_BRANCH || "", issue: SS_ISSUE || "",
  confidence: conf, status: "active", superseded: SS_SUPERSEDE || "", created_at: now
}
const file = SS_STATE + "/decisions.jsonl"
fs.appendFileSync(file, JSON.stringify(rec) + "\n", { encoding: "utf8", flag: "a" })

// Rebuild the active projection (tolerant read; newest first; cap 50).
const all = fs.readFileSync(file, "utf8").split("\n").filter(Boolean)
  .map((l) => { try { return JSON.parse(l) } catch { return null } }).filter(Boolean)
const retired = new Set(all.map((d) => d.superseded).filter(Boolean))
const active = all.filter((d) => !retired.has(d.id)).reverse()
fs.writeFileSync(SS_STATE + "/decisions.active.json",
  JSON.stringify({ updated_at: now, count: active.length, decisions: active.slice(0, 50) }, null, 2) + "\n")
console.log("DECISION_LOGGED: " + id)
console.log("ACTIVE_DECISIONS: " + active.length)
NODE
