#!/usr/bin/env bash
# Append one learning to .opencode/state/learnings.jsonl.
# Validates in node before writing: type enum, key shape, confidence clamped
# to the gstack guidance bands, and the injection screen. Append-only, O_APPEND.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.opencode/state"
mkdir -p "$STATE" 2>/dev/null || true

KEY="" STATEMENT="" TYPE="" CONF="" SOURCE="session"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --key) KEY="$2"; shift 2 ;;
    --statement) STATEMENT="$2"; shift 2 ;;
    --type) TYPE="$2"; shift 2 ;;
    --confidence) CONF="$2"; shift 2 ;;
    --source) SOURCE="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "$KEY" || -z "$STATEMENT" || -z "$TYPE" ]]; then
  echo "LEARNING_LOG_ERROR: need --key --statement --type"
  exit 0
fi

SS_STATE="$STATE" SS_KEY="$KEY" SS_STATEMENT="$STATEMENT" SS_TYPE="$TYPE" SS_CONF="$CONF" SS_SOURCE="$SOURCE" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE, SS_KEY, SS_STATEMENT, SS_TYPE, SS_CONF, SS_SOURCE } = process.env
const fail = (m) => { console.log("LEARNING_LOG_ERROR: " + m); process.exit(0) }

if (!["observed", "inferred", "user-stated"].includes(SS_TYPE))
  fail("type must be observed|inferred|user-stated")
if (!/^[a-z0-9][a-z0-9-]{0,63}$/.test(SS_KEY))
  fail("key must be kebab-case, 1-64 chars")

// gstack injection screen: a "learning" that reads like a prompt injection is
// not a learning.
const INJECTION_PATTERNS = [
  "ignore previous instructions", "ignore all previous", "you are now",
  "from now on", "do not report", "approve all", "system:", "assistant:", "developer:"
]
const low = SS_STATEMENT.toLowerCase()
const hit = INJECTION_PATTERNS.find((p) => low.includes(p))
if (hit) fail(`injection screen blocked (matched "${hit}")`)

// Confidence guidance: user-stated 10; observed 8-9; inference 4-5.
let conf = SS_CONF === "" ? null : Number(SS_CONF)
if (conf === null || Number.isNaN(conf))
  conf = SS_TYPE === "user-stated" ? 10 : SS_TYPE === "observed" ? 8 : 4
conf = Math.max(1, Math.min(10, Math.round(conf)))

const now = new Date().toISOString()
const id = "lrn-" + Date.now().toString(36) + Math.random().toString(36).slice(2, 6)
// "Records MUST serialize to a single line" — atomic append across processes.
const line = JSON.stringify({ id, key: SS_KEY, statement: SS_STATEMENT, type: SS_TYPE, confidence: conf, source: SS_SOURCE, created_at: now, updated_at: now, occurrences: 1, status: "active" })
fs.appendFileSync(SS_STATE + "/learnings.jsonl", line + "\n", { encoding: "utf8", flag: "a" })
console.log("LEARNING_LOGGED: " + id)
console.log("KEY: " + SS_KEY)
console.log("CONFIDENCE: " + conf + "/10")
NODE
