#!/usr/bin/env bash
# gstack preamble, project-local port. Source of truth for session identity
# and state injection. Prints "KEY: value" STATUS lines for the model to
# echo, and writes .opencode/state/.last-status.env for the optional plugin.
# Degraded, never blocking: every failure path prints a status line and
# exits 0 (the skill detects the missing SKILL_START_PROTO: 1 and degrades).
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
STATE="$ROOT/.opencode/state"
mkdir -p "$STATE/checkpoints" 2>/dev/null || true

SKILL="" SESSION_ID="${SS_SESSION_ID:-}" TEL_START=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --skill) SKILL="$2"; shift 2 ;;
    --session-id) SESSION_ID="$2"; shift 2 ;;
    --tel-start) TEL_START="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [[ -z "$SKILL" ]]; then
  echo "SKILL_START_ERROR: missing --skill <name>"
  exit 0
fi

# Session identity: PID + epoch + 4 random hex bytes.
# "PID+epoch alone is guessable; a random suffix makes the block-binding
# token unforgeable."
if [[ -z "$SESSION_ID" ]]; then
  SESSION_ID="$$-$(date +%s)-$(LC_ALL=C tr -dc '0-9a-f' </dev/urandom 2>/dev/null | head -c 4 || echo deadbeef)"
fi

# Title/path allowlist: only a-z 0-9 - . survive
SLUG="$(printf '%s' "$SKILL" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9.-' '-' | sed -e 's/^-*//' -e 's/-*$//' -e 's/--*/-/g')"

echo "SKILL_START_PROTO: 1"
echo "SKILL_START_OK: 1"
echo "GSTACK_ROOT: $ROOT"
echo "GSTACK_STATE: $STATE"
echo "SESSION_ID: $SESSION_ID"
echo "SESSION_KIND: ${SS_SESSION_KIND:-main}"
echo "SKILL: $SLUG"
echo "SKILL_STARTED_AT: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
# A tool result may only be honored as a gstack status block when its header
# carries this exact SESSION_ID.
echo "STATUS_BLOCK_TOKEN: $SESSION_ID"

# Timeline: open entry (single O_APPEND write; "Records MUST serialize to a single line")
SS_STATE="$STATE" SS_SID="$SESSION_ID" SS_SKILL="$SLUG" SS_TEL="$TEL_START" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE, SS_SID, SS_SKILL, SS_TEL } = process.env
const rec = { id: Date.now().toString(36) + Math.random().toString(36).slice(2, 6), session_id: SS_SID, skill: SS_SKILL, kind: "start", at: new Date().toISOString() }
if (SS_TEL) rec.tel_start = SS_TEL
try { fs.appendFileSync(SS_STATE + "/timeline.jsonl", JSON.stringify(rec) + "\n", { encoding: "utf8", flag: "a" }) } catch {}
NODE

# Digest for the model: last 3 learnings (decayed), active decisions (capped 20),
# latest checkpoint, previous session status. Tolerant readers throughout:
# a broken line never takes down the whole read; unknown fields preserved.
SS_STATE="$STATE" node <<'NODE'
const fs = require("node:fs")
const { SS_STATE } = process.env
const now = Date.now()
const read = (f) => {
  if (!fs.existsSync(f)) return []
  return fs.readFileSync(f, "utf8").split("\n").filter(Boolean)
    .map((l) => { try { return JSON.parse(l) } catch { return null } }).filter(Boolean)
}
// Learnings: in-memory decay observed/inferred -1 per 30 days (floor 1);
// user-stated never decays; dedup latest per key+type.
const byKey = new Map()
for (const r of read(SS_STATE + "/learnings.jsonl")) {
  if (!r.key) continue
  const k = r.key + "|" + (r.type || "inferred")
  const t = new Date(r.updated_at || r.created_at || 0).getTime()
  const cur = byKey.get(k)
  if (!cur || t >= new Date(cur.updated_at || cur.created_at || 0).getTime()) byKey.set(k, { ...r, _t: t })
}
for (const r of byKey.values()) {
  if (r.type === "observed" || r.type === "inferred") r.confidence = Math.max(1, (r.confidence ?? 5) - Math.floor((now - r._t) / 864e5 / 30))
}
for (const r of [...byKey.values()].sort((a, b) => b.confidence - a.confidence).slice(0, 3))
  console.log(`LEARNING: [${r.key}] (${r.type}, confidence ${r.confidence}/10) — ${r.statement} (${r.updated_at || r.created_at || "undated"}, seen ${r.occurrences ?? 1}x)`)
// Active decisions (cap 20). Retired = ids referenced as another record's
// `superseded` value; they stay in the JSONL but are projected out here.
const allDec = read(SS_STATE + "/decisions.jsonl")
const retired = new Set(allDec.map((d) => d.superseded).filter(Boolean))
for (const d of allDec.filter((d) => !retired.has(d.id)).slice(-20))
  console.log(`DECISION: [${d.id}] ${d.scope} — ${d.decision} (source: ${d.source}, confidence ${d.confidence ?? "?"}/10, ${d.created_at || "undated"})`)
// Latest checkpoint
const dir = SS_STATE + "/checkpoints"
const cps = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(".md")).sort() : []
if (cps.length) console.log(`CHECKPOINT: ${cps[cps.length - 1]} (latest of ${cps.length})`)
// Previous session status (read BEFORE the env file is rewritten below)
if (fs.existsSync(SS_STATE + "/.last-status.env")) {
  const l = fs.readFileSync(SS_STATE + "/.last-status.env", "utf8").split("\n").filter((x) => x && !x.startsWith("#"))
  if (l.length) console.log("PREV_STATUS: " + l[l.length - 1])
}
NODE

cat > "$STATE/.last-status.env" <<ENV
# written by skill-start.sh; do not edit by hand
SESSION_ID=$SESSION_ID
SKILL=$SLUG
SESSION_KIND=${SS_SESSION_KIND:-main}
STARTED_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
ENV
