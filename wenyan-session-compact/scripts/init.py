#!/usr/bin/env python3
"""
init.py — wenyan-session-compact project initializer

Purpose: One-time setup. Creates .wy-session/ at project root and installs
         SessionStart + PreCompact hooks into .claude/settings.json.

Dependencies: Python stdlib only (pathlib, json, subprocess, sys, io)
"""

import io
import json
import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ── Templates ────────────────────────────────────────────────────────────────

GLOBAL_STATE_TEMPLATE = """\
# 经 · Global State

---

## 道（方向性）

{项目核心方向}

---

## 名（名词性）

{关键术语}

---

## 定（定义性决策）

{已拍板决策}

---

## 弃（全局排除路径）

{已关闭路径}

---

## 知（工程约束）

{技术约束}

---

## 疑（当前张力）

{未决问题}

---

## 续（当前方向）

{下一步}
"""

SESSION_START_CMD = (
    "echo '' && "
    "echo '╔══════════════════════════════╗' && "
    "echo '║     WY SESSION START         ║' && "
    "echo '╚══════════════════════════════╝' && "
    "echo '' && "
    "echo '── 经 (GLOBAL STATE) ──────────' && "
    "cat .wy-session/global-state.md 2>/dev/null || echo '(not initialized — run init.py)' && "
    "echo '' && "
    "echo '── 册 (LAST SESSION) ──────────' && "
    "LATEST=$(ls -t .wy-session/sessions/*.md 2>/dev/null | head -1) && "
    '[ -n "$LATEST" ] && cat "$LATEST" || echo \'(no prior session)\' && '
    "echo '' && "
    "echo '══════════════════════════════' && "
    "echo 'Context loaded. Ready to work.' && "
    "echo '══════════════════════════════'"
)

PRECOMPACT_CMD = (
    "echo '' && "
    "echo '╔══════════════════════════════════════════════════════╗' && "
    "echo '║  CONTEXT AT THRESHOLD                                ║' && "
    "echo '║  Run /session-manager to compress before compacting  ║' && "
    "echo '╚══════════════════════════════════════════════════════╝'"
)

# Ruff formatter hook — --no-cache prevents .ruff_cache/ from being created
RUFF_CMD = (
    'python -c "import json,sys; d=json.load(sys.stdin); '
    "fp=d.get('tool_input',d).get('file_path',''); "
    "import subprocess; subprocess.run(['ruff','format','--no-cache',fp],"
    "capture_output=True) if fp.endswith('.py') else None\" 2>/dev/null || true"
)

# ── Path resolution ───────────────────────────────────────────────────────────


def get_project_root() -> Path:
    """Detect git repo root. Falls back to cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip())
    except Exception:
        pass
    return Path.cwd()


# ── Init steps ────────────────────────────────────────────────────────────────


def create_wy_session(project_root: Path) -> None:
    wy = project_root / ".wy-session"
    (wy / "sessions").mkdir(parents=True, exist_ok=True)

    gs = wy / "global-state.md"
    if not gs.exists():
        gs.write_text(GLOBAL_STATE_TEMPLATE, encoding="utf-8")
        print(f"✓ 经 created:   {gs}")
    else:
        print(f"  经 exists:    {gs}")

    print(f"✓ 册 dir ready: {wy / 'sessions'}")


def update_gitignore(project_root: Path) -> None:
    gitignore = project_root / ".gitignore"
    entry = ".wy-session/"
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8")
        if entry in content:
            print(f"  .gitignore: {entry} already present")
            return
        sep = "" if content.endswith("\n") else "\n"
        gitignore.write_text(content + sep + entry + "\n", encoding="utf-8")
    else:
        gitignore.write_text(entry + "\n", encoding="utf-8")
    print(f"✓ .gitignore ← {entry}")


def update_settings(project_root: Path) -> None:
    claude_dir = project_root / ".claude"
    claude_dir.mkdir(exist_ok=True)
    settings_path = claude_dir / "settings.json"

    data: dict = {}
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    hooks = data.setdefault("hooks", {})

    def hook_exists(hook_list: list, cmd: str) -> bool:
        return any(
            h.get("command") == cmd
            for entry in hook_list
            for h in entry.get("hooks", [])
        )

    ptu = hooks.setdefault("PostToolUse", [])
    if not hook_exists(ptu, RUFF_CMD):
        ptu.append(
            {
                "matcher": "Write|Edit",
                "hooks": [{"type": "command", "command": RUFF_CMD, "timeout": 10}],
            }
        )
        print("✓ PostToolUse ruff hook injected (--no-cache)")
    else:
        print("  PostToolUse ruff hook already present")

    ss = hooks.setdefault("SessionStart", [])
    if not hook_exists(ss, SESSION_START_CMD):
        ss.append(
            {
                "matcher": "",
                "hooks": [
                    {"type": "command", "command": SESSION_START_CMD, "timeout": 15}
                ],
            }
        )
        print("✓ SessionStart hook injected")
    else:
        print("  SessionStart hook already present")

    pc = hooks.setdefault("PreCompact", [])
    if not hook_exists(pc, PRECOMPACT_CMD):
        pc.append(
            {
                "matcher": "auto|manual",
                "hooks": [
                    {"type": "command", "command": PRECOMPACT_CMD, "timeout": 10}
                ],
            }
        )
        print("✓ PreCompact hook injected")
    else:
        print("  PreCompact hook already present")

    settings_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✓ Settings saved: {settings_path}")


# ── Entry point ───────────────────────────────────────────────────────────────


def main():
    root = get_project_root()
    print(f"\nwenyan-session-compact init")
    print(f"Project root: {root}\n")

    create_wy_session(root)
    update_gitignore(root)
    update_settings(root)

    print("\nDone. Restart Claude Code for hooks to take effect.")


if __name__ == "__main__":
    main()
