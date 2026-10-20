#!/usr/bin/env bash
# Tolerant reader for learnings.jsonl. A broken line never takes down the
# whole read; unknown fields are preserved. Applies in-memory decay
# (observed/inferred -1 per 30 days, floor 1; user-stated never decays),
# dedups to latest per key+type, and ranks by query-token overlap x confidence.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.opencode/state"

QUERY="" KEY="" LIMIT="10"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --query) QUERY="$2"; shift 2 ;;
    --key) KEY="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    *) shift ;;
  esac
done

SS_STATE="$STATE" SS_QUERY="$QUERY" SS_KEY="$KEY" SS_LIMIT="$LIMIT" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE, SS_QUERY, SS_KEY, SS_LIMIT } = process.env
const file = SS_STATE + "/learnings.jsonl"
if (!fs.existsSync(file)) { console.log("LEARNINGS: (none logged yet)"); process.exit(0) }
const now = Date.now()
const rows = fs.readFileSync(file, "utf8").split("\n").filter(Boolean)
  .map((l) => { try { return JSON.parse(l) } catch { return null } }).filter(Boolean)
// Dedup: latest per key+type
const byKey = new Map()
for (const r of rows) {
  if (!r.key) continue
  const k = r.key + "|" + (r.type || "inferred")
  const t = new Date(r.updated_at || r.created_at || 0).getTime()
  const cur = byKey.get(k)
  if (!cur || t >= new Date(cur.updated_at || cur.created_at || 0).getTime()) byKey.set(k, { ...r, _t: t })
}
let out = [...byKey.values()]
if (SS_KEY) out = out.filter((r) => r.key === SS_KEY)
// In-memory decay
for (const r of out) {
  if (r.type === "observed" || r.type === "inferred")
    r.confidence = Math.max(1, (r.confidence ?? 5) - Math.floor((now - r._t) / 864e5 / 30))
}
const tokens = (SS_QUERY || "").toLowerCase().split(/[^a-z0-9]+/).filter((t) => t.length > 2)
const score = (r) => {
  const hay = (r.key + " " + r.statement).toLowerCase()
  return tokens.length ? (tokens.filter((t) => hay.includes(t)).length / tokens.length) * r.confidence : r.confidence
}
if (tokens.length) out = out.filter((r) => score(r) > 0)
out.sort((a, b) => score(b) - score(a))
const top = out.slice(0, Number(SS_LIMIT) || 10)
if (!top.length) { console.log("LEARNINGS: (no match)"); process.exit(0) }
for (const r of top)
  console.log(`LEARNING: [${r.key}] (${r.type}, confidence ${r.confidence}/10) — ${r.statement} (${r.updated_at || r.created_at}, seen ${r.occurrences ?? 1}x)`)
NODE
