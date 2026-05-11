# AI Wiki — Claude Code 对话知识自动收集系统

每次 Claude Code 对话结束后，自动提取对话中的高价值知识（技术决策、bug 原因、配置变更、踩坑经验），用 AI 分类整理后写入 Obsidian vault。

## 工作原理

```
Claude Code 对话结束
       ↓
   Stop Hook 触发
       ↓
  收集脚本 (collect.py)
   ├── 读取 ~/.claude/history.jsonl 中的对话记录
   ├── 调用 AI API 提取四类知识
   └── 写入 Obsidian vault
       ├── concepts/    ← 知识页面
       ├── connections/ ← 跨主题洞察
       ├── index.md     ← 全局索引
       └── log.md       ← 操作日志
```

## 安装

### 1. 克隆仓库

```bash
git clone https://github.com/<your-username>/ai-wiki.git ~/ai_wiki
```

### 2. 安装依赖

```bash
pip install httpx pyyaml
```

### 3. 配置 API Key

在 `~/.claude/settings.json` 中确保有以下环境变量：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.longcat.chat/anthropic",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key-here",
    "ANTHROPIC_MODEL": "LongCat-2.0-Preview"
  }
}
```

> 支持任何兼容 Anthropic API 格式的服务（官方 Anthropic、LongCat 等）。

### 4. 配置 Stop Hook

在 `~/.claude/settings.json` 中添加（用 Python 脚本安全合并）：

```bash
python3 -c "
import json
with open('/home/$(whoami)/.claude/settings.json') as f:
    settings = json.load(f)
if 'hooks' not in settings:
    settings['hooks'] = {}
settings['hooks']['Stop'] = [
    {
        'matcher': '',
        'hooks': [
            {
                'type': 'command',
                'command': 'python3 /home/$(whoami)/ai_wiki/scripts/collect.py',
                'timeout': 60
            }
        ]
    }
]
with open('/home/$(whoami)/.claude/settings.json', 'w') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)
print('Hook configured.')
"
```

## Vault 结构

```
ai_wiki/
├── .wiki-schema      # 知识提取规则（告诉 AI 如何分类）
├── index.md          # 全局索引（自动更新）
├── log.md            # 操作日志（自动追加）
├── concepts/         # 知识页面（每个知识点一篇）
└── connections/      # 跨主题洞察
```

## .wiki-schema 说明

定义了四类知识的提取规则：

| 类型 | 判断标准 |
|------|----------|
| **技术决策** | 涉及工具/框架/架构的选择或切换，有方案对比 |
| **bug原因** | 包含报错信息、排查过程、定位到根因 |
| **配置变更** | 修改配置文件、环境变量、安装/卸载软件包 |
| **踩坑经验** | 认知偏差记录、避坑建议、最佳实践 |

## 适配第三方 API

本项目使用 `httpx` 直接发 HTTP 请求，通过 `Authorization: Bearer` header 认证，兼容以下服务：

- Anthropic 官方 API
- LongCat API (`api.longcat.chat`)
- 其他 Anthropic 兼容层

如果使用 Anthropic 官方 API，将 `base_url` 留空或设为 `https://api.anthropic.com` 即可。

## 注意事项

- 每次对话结束后自动运行，无需手动触发
- 如果对话中没有提取到知识，会记录 `skipped` 状态
- `concepts/` 中的文件按知识点标题命名，重复标题会覆盖
