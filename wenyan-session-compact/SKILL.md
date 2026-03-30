---
name: wenyan-session-compact
version: 1.0.0
description: |
  Cross-session cognitive relay using Classical Chinese (wenyan) as a semantic
  compression medium. Compresses conversation chains into dense snapshots (册 cè)
  and distills them into persistent global state (经 jīng) that pre-fills the next
  session — no re-derivation needed.
  Trigger: session end · /session-manager · cognitive snapshot requested · project init
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - AskUserQuestion
---

## Preamble (runs when skill is triggered)

```bash
_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
_SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%H%M%S)}"
echo "Branch: $_BRANCH | Session: $_SESSION_ID"
echo "--- Recent sessions ---"
ls -t .wy-session/sessions/*.md 2>/dev/null | head -5 || echo "(no sessions yet — run init first)"
```

---

# wenyan-session-compact

## Why This Works

Every AI instance starts blank. Without a relay, each new session re-derives decisions
already made, re-opens closed paths, and loses reasoning momentum.

This skill compresses conversation state into a transferable semantic package.
The next instance reads it and picks up exactly where the last one left off.

**Why Classical Chinese (wenyan)?**

Wenyan maps directly onto pre-expanded semantic regions in the model — no decompression
needed. Its four-character syntax marks decision-unit boundaries naturally. Token density
is roughly 5× higher than modern prose, with ~85–90% semantic retention.

The `弃X取Y` (abandon X, take Y) pattern carries excluded paths explicitly —
the next instance reads them and does not re-propose dead options.

∴ Wenyan is the optimal compression medium for AI-to-AI semantic transfer,
not a stylistic choice.

---

## What to Record

Priority order (highest value first):

```
Excluded paths   — what was considered and why it was closed. Highest value. Never omit.
Decision rationale — why this over that. Without it, decisions become isolated facts.
Reasoning shifts — how thinking changed (起承转合 arc). Write when a pivot occurred.
Cognitive position — where thinking is pointed next.
Concrete actions — changes made to the world (file paths, commit hashes — keep modern format).
New knowledge — facts, definitions, naming decisions from this session.
```

**Do not record**: anything reconstructable from code or docs · resolved details
that don't affect future decisions.

---

## Structure

```
简 (jiǎn)  — atomic unit. One proposition per 简. Self-contained, context-independent.
册 (cè)    — one session, one file. sessions/{date}_{id}.md. Full record, never compressed.
经 (jīng)  — distilled global state. global-state.md. Updated after each session.
```

**册**: complete cognitive trace of one session. Raw, preserved, never overwritten.
**经**: big-picture only — direction, definitions, key decisions. Living document.

Both live in `.wy-session/` at the project root (created by init).

---

## Phase 0 — INIT (first time only)

Triggered when the user asks to initialize a project or when `.wy-session/` does not exist.

**Before running anything, show the user what will happen:**

```
Project root: /path/to/project

Will create:
  .wy-session/global-state.md    ← 经 template (empty)
  .wy-session/sessions/          ← 册 directory
  .claude/settings.json          ← add SessionStart + PreCompact hooks
  .gitignore                     ← add .wy-session/

Proceed?
```

Wait for explicit confirmation. Then run:

```bash
python .claude/skills/wenyan-session-compact/scripts/init.py
```

After init, instruct the user to restart Claude Code for hooks to take effect.
Then ask them to fill in the `## 道` section of `.wy-session/global-state.md`
with the project's core direction — this is the first 经 entry.

---

## Phase 1 — SESSION START

The SessionStart hook (installed by init) loads 经 and the latest 册 automatically.
No manual action needed. Read the loaded state and continue working.

If `.wy-session/` is missing, prompt the user to run init (Phase 0).

---

## Phase 2 — SESSION END · Write 册

At session end, review the full conversation once and write the 册 file.

```bash
python .claude/skills/wenyan-session-compact/scripts/cli.py new
```

Write 简 entries using the template in `assets/template.md`.

**Writing order**: 弃 (excluded paths) → 定 (decisions) → 演 (reasoning shifts, if any)
→ 为 (actions) → 知 (new knowledge) → 疑 (open tensions) → 续 (next direction)

**演 (reasoning shift arc)** — write when a significant pivot occurred in this session.
Use 起承转合 structure: opening position → development → turning point → resolution.
Focus on the 转 (turn): what caused the shift. Skip for purely execution sessions.

**QUICK_SAVE mode** — if the session was short or only directional: write one 续 entry only.

---

## Phase 3 — DISTILL · Update 经

Review each 简 in the new 册. Apply this filter:

> If this 简 disappeared, would the next instance make a wrong decision or re-open a closed path?

- **Qualifies** (directional / definitional / naming) → compare against current 经
- **No conflict** → merge into the relevant section of `global-state.md`
- **Conflict found** → pause. Present both versions via AskUserQuestion. Write the resolution as a 定 简 before updating 经.
- **Does not qualify** → stays in 册, not promoted

**Conflict types**:
```
定 ↔ 定   two decisions contradict
知 ↔ 知   two facts contradict
弃 → 定   a previously excluded path is now adopted
疑 ↔ 定   an open question was closed in an unexpected way
```

Never silently overwrite. Conflicts are information — surface them.

---

## Completion States

```
DONE               册 written, 经 updated, session fully archived
QUICK_SAVE         只写续简 — full review deferred to next session
DONE_WITH_CONFLICT conflict recorded, 经 update pending user resolution
```
