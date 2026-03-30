#!/usr/bin/env python3
"""
Session Manager CLI — 创建和管理 session 文件（册）。

Purpose: 按命名约定创建新的 session 文件，供 AI 填入文言简内容。
         会话 ID 优先取 CLAUDE_SESSION_ID 环境变量，fallback 到时间戳。
         路径指向项目根目录的 .wy-session/（由 init.py 创建）。

Dependencies: Python stdlib only (pathlib, argparse, datetime, os, subprocess, sys)
"""

import argparse
import io
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows console may default to cp1252 — force utf-8 for Chinese output
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def get_wy_session_dir() -> Path:
    """Resolve .wy-session/ at git root. Falls back to cwd."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Path(result.stdout.strip()) / ".wy-session"
    except Exception:
        pass
    return Path.cwd() / ".wy-session"


WY_SESSION_DIR = get_wy_session_dir()
SESSIONS_DIR = WY_SESSION_DIR / "sessions"
GLOBAL_STATE_FILE = WY_SESSION_DIR / "global-state.md"


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today():
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_session_id():
    """获取 Claude Code session ID，fallback 到时间戳后六位。"""
    sid = os.environ.get("CLAUDE_SESSION_ID", "").strip()
    if sid:
        return sid[:12]
    return datetime.now(timezone.utc).strftime("%H%M%S")


def cmd_new(args):
    """创建新的 session 文件（册）。"""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    session_id = get_session_id()
    filename = f"{today()}_{session_id}.md"
    filepath = SESSIONS_DIR / filename

    if filepath.exists():
        print(f"已存在：{filepath}")
        return

    content = f"# 册 · {today()} · {session_id}\n元：{now_iso()}\n\n---\n\n"
    filepath.write_text(content, encoding="utf-8")
    print(f"册已创建：{filepath}")
    print(f"参考 template.md 的锚点约定，将简内容写入此文件。")


def cmd_state(args):
    """显示当前 global-state（经）。"""
    if GLOBAL_STATE_FILE.exists():
        print(GLOBAL_STATE_FILE.read_text(encoding="utf-8"))
    else:
        print("经尚未初始化。")


def cmd_list(args):
    """列出所有 session 文件（册）。"""
    if not SESSIONS_DIR.exists() or not any(SESSIONS_DIR.iterdir()):
        print("暂无 session 记录。")
        return
    files = sorted(SESSIONS_DIR.glob("*.md"), reverse=True)
    for f in files:
        print(f.name)


def main():
    parser = argparse.ArgumentParser(
        prog="cli.py",
        description="Session Manager CLI — 认知接力工具",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("new", help="创建新 session 文件（册）")
    sub.add_parser("state", help="显示 global-state（经）")
    sub.add_parser("list", help="列出所有 session 记录")

    args = parser.parse_args()

    if args.command == "new":
        cmd_new(args)
    elif args.command == "state":
        cmd_state(args)
    elif args.command == "list":
        cmd_list(args)


if __name__ == "__main__":
    main()
