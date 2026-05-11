# AI Wiki — Claude Code Plugin

每次 Claude Code 对话结束后，自动提取对话中的高价值知识（技术决策、bug 原因、配置变更、踩坑经验），用 AI 分类整理后写入 Obsidian vault。

## 安装

### 方式一：从 GitHub 安装（推荐）

```bash
# 1. 克隆 plugin
git clone https://github.com/zarttic/ai-wiki.git ~/.claude/plugins/ai-wiki

# 2. 运行安装脚本
python3 ~/.claude/plugins/ai-wiki/scripts/install.py
```

### 方式二：手动安装

```bash
# 1. 创建 vault 目录
mkdir -p ~/ai_wiki/{concepts,connections}

# 2. 复制 plugin
cp -r ai-wiki ~/.claude/plugins/ai-wiki

# 3. 配置 Stop Hook（见下方）
```

### 配置 Stop Hook

在 `~/.claude/settings.json` 中添加：

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/plugins/ai-wiki/scripts/collect.py",
            "timeout": 120
          }
        ]
      }
    ]
  }
}
```

### 配置 API Key

在 `~/.claude/settings.json` 的 `env` 中配置：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.longcat.chat/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "ANTHROPIC_MODEL": "LongCat-2.0-Preview"
  }
}
```

> 支持任何兼容 Anthropic API 格式的服务（官方 Anthropic、LongCat 等）。

## 使用

安装完成后，每次 Claude Code 对话结束时会自动：

1. 读取对话记录
2. 调用 AI 提取四类知识
3. 写入 `~/ai_wiki/concepts/` 目录
4. 更新 `~/ai_wiki/index.md` 索引
5. 追加 `~/ai_wiki/log.md` 日志

## Vault 结构

```
~/ai_wiki/
├── index.md          # 全局索引（自动更新）
├── log.md            # 操作日志（自动追加）
├── concepts/         # 知识页面（每个知识点一篇）
└── connections/      # 跨主题洞察
```

## 跨平台兼容性

| 特性 | Linux/Mac | Windows |
|------|-----------|---------|
| Vault 路径 | `~/ai_wiki` | `%USERPROFILE%\ai_wiki` |
| Python 命令 | `python3` | `python` |
| Claude 目录 | `~/.claude` | `%USERPROFILE%\.claude` |

## 仓库结构

| 仓库 | 可见性 | 内容 |
|------|--------|------|
| **ai-wiki** | 公开 | Plugin 源码，可分享 |
| **ai-wiki-vault** | 私有 | 个人知识库 |

代码和知识库分离，`concepts/` 和 `connections/` 中的内容不会被提交到公开仓库。
