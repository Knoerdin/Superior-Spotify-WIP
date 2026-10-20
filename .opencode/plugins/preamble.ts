// .opencode/plugins/preamble.ts — OPTIONAL, Phase 0-verified.
// Prompt-admission approximation of the gstack preamble. The bash script
// (scripts/skill-start.sh) remains the source of truth; this appends the same
// state digest to the admitted prompt so the model sees project memory without
// waiting for Step 0. V2 admission has NO typed rejection and is retry-safe
// but not exactly-once, so the draft dedupes with a marker and never throws.
//
// PHASE-0 VERDICT (verified 2026-10-20 against opencode v2.1.1 in a scratch
// project): node:fs imports in the plugin runtime; ctx.location.directory is
// the project dir (process.cwd() is NOT — do not use it); prompt text
// mutation reaches the model. If any of these breaks on upgrade, the plugin
// no-ops on all errors and every skill still works via its Step 0 bash call.
import { Plugin } from "@opencode/plugin"
import fs from "node:fs"
import path from "node:path"

const MARKER = "GSTACK-PREAMBLE"

export default Plugin.define({
  id: "gstack-preamble",
  setup(ctx) {
    // Resolve the project root from the verified ctx surface, not process.cwd().
    const root = ctx.location?.directory
    if (!root) return // no location: do nothing; the skill's Step 0 handles it

    return ctx.session.hook("prompt", async (event) => {
      try {
        const text = String(event.prompt?.text ?? "")
        if (text.includes(MARKER)) return // already injected (retry-safe)

        const state = path.join(root, ".opencode", "state")
        if (!fs.existsSync(state)) return // nothing to inject yet

        const lines: string[] = [
          "",
          "## GSTACK PREAMBLE",
          `<!-- ${MARKER}: session state digest. The skill's Step 0 bash call is authoritative and supersedes this. -->`,
        ]

        // Last session status
        if (fs.existsSync(path.join(state, ".last-status.env"))) {
          const last = fs
            .readFileSync(path.join(state, ".last-status.env"), "utf8")
            .split("\n")
            .filter((l) => l && !l.startsWith("#"))
            .pop()
          if (last) lines.push("PREV_STATUS: " + last)
        }
        // Active decisions (cap 20)
        if (fs.existsSync(path.join(state, "decisions.active.json"))) {
          const doc = JSON.parse(fs.readFileSync(path.join(state, "decisions.active.json"), "utf8"))
          for (const d of (doc.decisions ?? []).slice(-20)) {
            lines.push(`DECISION: [${d.id}] ${d.scope} — ${d.decision} (source: ${d.source}, confidence ${d.confidence}/10, ${d.created_at})`)
          }
        }
        // Last 3 learnings, decayed (observed/inferred -1 per 30d, floor 1)
        if (fs.existsSync(path.join(state, "learnings.jsonl"))) {
          const now = Date.now()
          const rows = fs
            .readFileSync(path.join(state, "learnings.jsonl"), "utf8")
            .split("\n")
            .filter(Boolean)
            .map((l) => {
              try {
                return JSON.parse(l)
              } catch {
                return null
              }
            })
            .filter(Boolean)
          const byKey = new Map()
          for (const r of rows) {
            if (!r.key) continue
            const k = r.key + "|" + (r.type || "inferred")
            const t = new Date(r.updated_at || r.created_at || 0).getTime()
            const cur = byKey.get(k)
            if (!cur || t >= new Date(cur.updated_at || cur.created_at || 0).getTime()) byKey.set(k, r)
          }
          const top = [...byKey.values()]
            .map((r) => {
              const c =
                r.type === "user-stated"
                  ? r.confidence
                  : Math.max(1, (r.confidence ?? 5) - Math.floor((now - new Date(r.updated_at || r.created_at || 0).getTime()) / 864e5 / 30))
              return { ...r, confidence: c }
            })
            .sort((a, b) => b.confidence - a.confidence)
            .slice(0, 3)
          for (const r of top) lines.push(`LEARNING: [${r.key}] (${r.type}, confidence ${r.confidence}/10) — ${r.statement}`)
        }
        // Latest checkpoint
        const cps = fs.existsSync(path.join(state, "checkpoints"))
          ? fs.readdirSync(path.join(state, "checkpoints")).filter((f) => f.endsWith(".md")).sort()
          : []
        if (cps.length) lines.push(`CHECKPOINT: ${cps[cps.length - 1]} (latest of ${cps.length})`)

        event.prompt.text = text + "\n" + lines.join("\n")
      } catch {
        // degraded mode: skip injection silently; the skill's Step 0 handles it.
      }
    })
  },
})
