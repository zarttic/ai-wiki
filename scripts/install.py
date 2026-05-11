#!/usr/bin/env python3
"""
AI Wiki Plugin Installer
一键安装 ai-wiki plugin 并配置 Stop Hook。
"""

import json
import os
import platform
import shutil
import sys
from pathlib import Path


def main():
    home = Path.home()
    claude_dir = home / ".claude"
    settings_path = claude_dir / "settings.json"
    vault_dir = home / "ai_wiki"
    plugin_dir = Path(__file__).parent.parent  # scripts/ -> plugin root

    print("=" * 50)
    print("  AI Wiki Plugin Installer")
    print("=" * 50)

    # 1. 创建 vault 目录
    print(f"\n[1/4] 创建 vault 目录: {vault_dir}")
    (vault_dir / "concepts").mkdir(parents=True, exist_ok=True)
    (vault_dir / "connections").mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {vault_dir}/concepts/")
    print(f"  ✓ {vault_dir}/connections/")

    # 2. 复制 plugin 到标准位置（如果不在的话）
    print(f"\n[2/4] 确认 plugin 位置")
    standard_plugin_dir = claude_dir / "plugins" / "cache" / "ai-wiki" / "1.0.0"
    if plugin_dir.resolve() != standard_plugin_dir.resolve():
        standard_plugin_dir.parent.mkdir(parents=True, exist_ok=True)
        if standard_plugin_dir.exists():
            shutil.rmtree(standard_plugin_dir)
        shutil.copytree(plugin_dir, standard_plugin_dir)
        print(f"  ✓ Plugin 复制到: {standard_plugin_dir}")
    else:
        print(f"  ✓ Plugin 已在标准位置: {plugin_dir}")

    # 3. 配置 Stop Hook
    print(f"\n[3/4] 配置 Stop Hook")

    # 读取现有配置
    if settings_path.exists():
        with open(settings_path) as f:
            settings = json.load(f)
    else:
        settings = {}

    # 确定 Python 命令
    py_cmd = "python" if platform.system() == "Windows" else "python3"
    collect_script = standard_plugin_dir / "scripts" / "collect.py"

    # 添加 hooks
    if "hooks" not in settings:
        settings["hooks"] = {}

    hook_cmd = f'{py_cmd} "{collect_script}"'
    settings["hooks"]["Stop"] = [
        {
            "matcher": "",
            "hooks": [
                {
                    "type": "command",
                    "command": hook_cmd,
                    "timeout": 120
                }
            ]
        }
    ]

    with open(settings_path, "w") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Stop Hook: {hook_cmd}")
    print(f"  ✓ 配置写入: {settings_path}")

    # 4. 检查 API 配置
    print(f"\n[4/4] 检查 API 配置")
    env = settings.get("env", {})
    has_base_url = "ANTHROPIC_BASE_URL" in env
    has_token = "ANTHROPIC_AUTH_TOKEN" in env
    has_model = "ANTHROPIC_MODEL" in env

    if has_token and has_model:
        print(f"  ✓ API Token: {env['ANTHROPIC_AUTH_TOKEN'][:10]}...")
        print(f"  ✓ Model: {env.get('ANTHROPIC_MODEL', 'default')}")
        if has_base_url:
            print(f"  ✓ Base URL: {env['ANTHROPIC_BASE_URL']}")
    else:
        print("  ⚠ API Key 未配置！")
        print(f"  请编辑 {settings_path}，在 env 中添加：")
        print(f'    "ANTHROPIC_AUTH_TOKEN": "your-api-key"')
        print(f'    "ANTHROPIC_MODEL": "your-model-name"')

    # 完成
    print(f"\n{'=' * 50}")
    print("  安装完成！")
    print(f"{'=' * 50}")
    print(f"\n  Vault 目录: {vault_dir}")
    print(f"  Hook 命令: {hook_cmd}")
    print(f"\n  开始对话后，知识会自动提取到 vault 中。")
    print(f"  查看 {vault_dir}/index.md 浏览知识点。")


if __name__ == "__main__":
    main()
