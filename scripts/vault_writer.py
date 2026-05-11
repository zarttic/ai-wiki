"""AI Wiki — Vault 写入模块。"""

import os
import re
from datetime import datetime, timezone, timedelta
from collections import defaultdict


def slugify(title: str) -> str:
    slug = title.lower().strip()
    slug = re.sub(r"\s+", "-", slug)
    slug = re.sub(r"[^a-z0-9一-鿿\-]", "", slug)
    slug = re.sub(r"-{2,}", "-", slug)
    return slug.strip("-")


def write_concept(concept: dict, vault_dir: str) -> str:
    """写入单个 concept 到 concepts/，返回文件路径。"""
    concepts_dir = os.path.join(vault_dir, "concepts")
    os.makedirs(concepts_dir, exist_ok=True)

    slug = slugify(concept["title"])
    filepath = os.path.join(concepts_dir, f"{slug}.md")

    tz = timezone(timedelta(hours=8))
    created = datetime.now(tz).strftime("%Y-%m-%d")

    lines = [
        f"# {concept['title']}",
        "",
        f"**类型**: {concept['type']}",
        f"**标签**: {', '.join(concept.get('tags', []))}",
        f"**创建**: {created}",
        "",
        "## 描述",
        concept.get("description", ""),
        "",
        "## 详细内容",
        concept.get("content", ""),
        "",
    ]

    if concept.get("commands"):
        lines += ["## 相关命令/代码", "```bash", concept["commands"], "```", ""]

    if concept.get("related"):
        lines += ["## 关联", ""]
        for r in concept["related"]:
            lines.append(f"- [[{r}]]")
        lines.append("")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


def update_index(vault_dir: str):
    """扫描 concepts/ 和 connections/，重建 index.md。"""
    concepts_dir = os.path.join(vault_dir, "concepts")
    connections_dir = os.path.join(vault_dir, "connections")

    # 收集 concepts 并按类型分组
    by_type = defaultdict(list)
    concept_count = 0
    if os.path.isdir(concepts_dir):
        for fname in sorted(os.listdir(concepts_dir)):
            if fname.endswith(".md") and fname != ".gitkeep":
                concept_count += 1
                path = os.path.join(concepts_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                ctype = "其他"
                for line in content.split("\n"):
                    if line.startswith("**类型**:"):
                        ctype = line.split(":", 1)[1].strip()
                        break
                title = fname[:-3]
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                desc = ""
                in_desc = False
                for line in content.split("\n"):
                    if line.strip() == "## 描述":
                        in_desc = True
                        continue
                    if in_desc:
                        if line.startswith("## "):
                            break
                        desc = line.strip()
                        break
                by_type[ctype].append((title, fname[:-3], desc))

    # 收集 connections
    connection_count = 0
    connections = []
    if os.path.isdir(connections_dir):
        for fname in sorted(os.listdir(connections_dir)):
            if fname.endswith(".md") and fname != ".gitkeep":
                connection_count += 1
                path = os.path.join(connections_dir, fname)
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                title = fname[:-3]
                for line in content.split("\n"):
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                connections.append((title, fname[:-3]))

    # 写 index.md
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    out = ["# AI Wiki Index", "", "## Concepts", ""]
    if not by_type:
        out.append("_暂无知识条目，等待对话收集。_")
    else:
        for ctype, items in sorted(by_type.items()):
            out.append(f"### {ctype}")
            out.append("")
            for title, slug, desc in items:
                desc_str = f" — {desc}" if desc else ""
                out.append(f"- [[{slug}]]{desc_str}")
            out.append("")

    out += ["## Connections", ""]
    if not connections:
        out.append("_暂无跨主题洞察。_")
    else:
        for title, slug in connections:
            out.append(f"- [[{slug}]] — {title}")
        out.append("")

    out += [
        "## Stats",
        f"- Total concepts: {concept_count}",
        f"- Total connections: {connection_count}",
        f"- Last updated: {now}",
    ]

    with open(os.path.join(vault_dir, "index.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def append_log(vault_dir: str, session_id: str, concepts_extracted: list[dict],
               messages_count: int, skipped: bool = False):
    """追加日志到 log.md。"""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    lines = [
        f"\n## {now}",
        f"- Session: {session_id[:8]}...",
        f"- Messages: {messages_count}",
    ]

    if skipped:
        lines.append("- Status: skipped (no valuable knowledge)")
    elif concepts_extracted:
        lines.append(f"- Extracted: {len(concepts_extracted)} concepts")
        for c in concepts_extracted:
            lines.append(f"  - {c.get('title', '?')} ({c.get('type', '?')})")
    else:
        lines.append("- Status: no concepts extracted")

    lines.append("")

    log_path = os.path.join(vault_dir, "log.md")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write("\n".join(lines))
