---
description: Install ai-wiki plugin and configure Stop Hook
allowed-tools: [Read, Write, Bash, Glob]
---

# Install ai-wiki

安装 ai-wiki 插件并配置 Stop Hook，让每次 Claude Code 对话结束后自动提取知识。

## 步骤

### 1. 确认 vault 目录

Vault 默认创建在 `~/ai_wiki/`。如果已存在则跳过。

```bash
mkdir -p ~/ai_wiki/{concepts,connections}
```

### 2. 将 plugin 复制到 Claude Code 插件目录

```bash
PLUGIN_DIR="$HOME/.claude/plugins/cache/ai-wiki/1.0.0"
mkdir -p "$PLUGIN_DIR"
cp -r "${CLAUDE_PLUGIN_ROOT:-.}"/* "$PLUGIN_DIR/"
```

### 3. 配置 Stop Hook

运行以下 Python 脚本，安全地将 Stop Hook 合并到 `~/.claude/settings.json`：

```bash
python3 << 'PYEOF'
import json, os

settings_path = os.path.join(os.path.expanduser("~"), ".claude", "settings.json")
plugin_root = os.path.join(os.path.expanduser("~"), ".claude", "plugins", "cache", "ai-wiki", "1.0.0")

# 读取现有配置（如果不存在则创建）
if os.path.exists(settings_path):
    with open(settings_path) as f:
        settings = json.load(f)
else:
    settings = {}

# 添加 env 配置（如果用户还没有配置 API key）
if "env" not in settings:
    settings["env"] = {}

# 添加 hooks 配置
if "hooks" not in settings:
    settings["hooks"] = {}

# 构建 collect.py 路径（兼容 Windows）
import platform
if platform.system() == "Windows":
    py_cmd = "python"
else:
    py_cmd = "python3"

collect_cmd = f'{py_cmd} "{plugin_root}/scripts/collect.py"'

settings["hooks"]["Stop"] = [
    {
        "matcher": "",
        "hooks": [
            {
                "type": "command",
                "command": collect_cmd,
                "timeout": 120
            }
        ]
    }
]

# 写回
with open(settings_path, "w") as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print(f"Stop Hook configured: {collect_cmd}")
print(f"Settings saved to: {settings_path}")
PYEOF
```

### 4. 验证安装

```bash
# 检查 hook 是否配置成功
python3 -c "
import json, os
with open(os.path.expanduser('~/.claude/settings.json')) as f:
    d = json.load(f)
hooks = d.get('hooks', {}).get('Stop', [])
if hooks:
    print('Stop Hook configured:', hooks[0]['hooks'][0]['command'])
else:
    print('ERROR: Stop Hook not found')
"
```

## 安装完成后

- 每次 Claude Code 对话结束后，会自动提取知识并写入 `~/ai_wiki/concepts/`
- 查看 `~/ai_wiki/index.md` 浏览所有知识点
- 查看 `~/ai_wiki/log.md` 查看收集日志

## 配置 API Key

在 `~/.claude/settings.json` 的 `env` 中配置：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://your-api-endpoint.com",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_MODEL": "your-model-name"
  }
}
```

> 支持任何兼容 Anthropic API 格式的服务。
