#!/usr/bin/env bash
# Tolerant reader for the decision log. --list-active (default) prints the
# active projection; --query filters; a broken line never takes down the read.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.opencode/state"

MODE="list-active" QUERY="" LIMIT="20"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --list-active) MODE="list-active"; shift ;;
    --query) MODE="query"; QUERY="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SS_STATE="$STATE" SS_MODE="$MODE" SS_QUERY="$QUERY" SS_LIMIT="$LIMIT" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE, SS_MODE, SS_QUERY, SS_LIMIT } = process.env
const file = SS_STATE + "/decisions.jsonl"
if (!fs.existsSync(file)) { console.log("DECISIONS: (none logged yet)"); process.exit(0) }
const all = fs.readFileSync(file, "utf8").split("\n").filter(Boolean)
  .map((l) => { try { return JSON.parse(l) } catch { return null } }).filter(Boolean)
let out = all
if (SS_MODE === "list-active") {
  const retired = new Set(all.map((d) => d.superseded).filter(Boolean))
  out = all.filter((d) => !retired.has(d.id)).reverse()
} else {
  const tokens = (SS_QUERY || "").toLowerCase().split(/[^a-z0-9]+/).filter((t) => t.length > 2)
  out = tokens.length
    ? all.filter((d) => { const hay = (d.decision + " " + d.rationale).toLowerCase(); return tokens.some((t) => hay.includes(t)) })
    : all.reverse()
}
const top = out.slice(0, Number(SS_LIMIT) || 20)
if (!top.length) { console.log("DECISIONS: (no match)"); process.exit(0) }
for (const d of top)
  console.log(`DECISION: [${d.id}] ${d.scope} — ${d.decision} (source: ${d.source}, confidence ${d.confidence ?? "?"}/10, ${d.created_at}${d.superseded ? `, supersedes ${d.superseded}` : ""})`)
NODE
