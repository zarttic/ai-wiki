#!/usr/bin/env python3
"""AI Wiki Collect — 主入口。Stop Hook 触发。"""

import json
import os
import sys

# 确保脚本所在目录在 PATH 中（plugin 运行时工作目录可能不同）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

HOME = os.path.expanduser("~")
CLAUDE_DIR = os.path.join(HOME, ".claude")
HISTORY_FILE = os.path.join(CLAUDE_DIR, "history.jsonl")
SESSIONS_DIR = os.path.join(CLAUDE_DIR, "sessions")

# Vault 路径：Windows 和 Linux/Mac 统一放在 ~/ai_wiki
VAULT_DIR = os.path.join(HOME, "ai_wiki")

# 从 settings.json 的 env 中加载 API 配置（hook 运行时 os.environ 不含这些变量）
_SETTINGS_FILE = os.path.join(CLAUDE_DIR, "settings.json")
if os.path.exists(_SETTINGS_FILE):
    try:
        with open(_SETTINGS_FILE) as _f:
            _cfg = json.load(_f)
        for _k, _v in _cfg.get("env", {}).items():
            os.environ.setdefault(_k, _v)
    except (json.JSONDecodeError, OSError):
        pass


def get_current_session_id() -> str:
    """读取最近活跃的 session ID。"""
    session_files = [f for f in os.listdir(SESSIONS_DIR) if f.endswith(".json")]
    if not session_files:
        return os.environ.get("CLAUDE_SESSION_ID", "")

    sessions = []
    for f in session_files:
        path = os.path.join(SESSIONS_DIR, f)
        try:
            with open(path) as fh:
                data = json.load(fh)
            sessions.append((data.get("updatedAt", 0), data.get("sessionId", "")))
        except (json.JSONDecodeError, KeyError):
            continue

    sessions.sort(reverse=True)
    return sessions[0][1] if sessions else ""


def read_session_messages(session_id: str) -> list[str]:
    """从 history.jsonl 读取指定 session 的消息。"""
    messages = []
    if not os.path.exists(HISTORY_FILE):
        return messages
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("sessionId") == session_id:
                    display = entry.get("display", "")
                    if display and len(display) > 2:
                        messages.append(display)
            except json.JSONDecodeError:
                continue
    return messages


def main():
    session_id = get_current_session_id()
    if not session_id:
        print("[ai-wiki] No session found, skipping.")
        sys.exit(0)

    messages = read_session_messages(session_id)
    if not messages:
        print(f"[ai-wiki] No messages for session {session_id[:8]}, skipping.")
        sys.exit(0)

    print(f"[ai-wiki] Session {session_id[:8]}: {len(messages)} messages.")

    # 调用 AI 提取
    try:
        from extract_knowledge import extract_knowledge
        concepts = extract_knowledge(messages)
    except Exception as e:
        print(f"[ai-wiki] Extraction failed: {e}", file=sys.stderr)
        from vault_writer import append_log
        append_log(VAULT_DIR, session_id, [], len(messages), skipped=True)
        sys.exit(0)

    if not concepts:
        print("[ai-wiki] No knowledge extracted.")
        from vault_writer import append_log
        append_log(VAULT_DIR, session_id, [], len(messages), skipped=True)
        sys.exit(0)

    print(f"[ai-wiki] Extracted {len(concepts)} concepts.")

    # 写入 vault
    from vault_writer import write_concept, update_index, append_log
    for concept in concepts:
        concept["source"] = session_id[:8]
        filepath = write_concept(concept, VAULT_DIR)
        print(f"[ai-wiki] Written: {filepath}")

    update_index(VAULT_DIR)
    append_log(VAULT_DIR, session_id, concepts, len(messages))
    print("[ai-wiki] Done.")


if __name__ == "__main__":
    main()
