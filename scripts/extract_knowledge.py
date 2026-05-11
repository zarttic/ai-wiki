"""AI Wiki — 知识提取模块。调用 Anthropic API 提取结构化知识。"""

import json
import os
import re
import yaml

VAULT_DIR = os.path.join(os.path.expanduser("~"), "ai_wiki")
SCHEMA_FILE = os.path.join(VAULT_DIR, ".wiki-schema")


def load_schema() -> dict:
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_extraction_prompt(schema: dict, messages: list[str]) -> str:
    rules = []
    for item in schema.get("extract", []):
        criteria = "\n".join(f"  - {c}" for c in item.get("criteria", []))
        examples = "\n".join(f"  - {e}" for e in item.get("examples", []))
        rules.append(f"### {item['name']}\n判断标准：\n{criteria}\n示例：\n{examples}")

    conversation = "\n".join(f"[{i+1}] {m}" for i, m in enumerate(messages))

    return f"""你是一个知识提取助手。分析以下对话，提取高价值技术知识。

## 提取规则

{chr(10).join(rules)}

## 对话记录

{conversation}

## 输出要求

1. 无有价值知识则返回 `[]`
2. 有则返回 JSON 数组，每个元素：

```json
[{{
  "title": "简短标题(5-15字)",
  "type": "技术决策|bug原因|配置变更|踩坑经验",
  "tags": ["标签1", "标签2"],
  "description": "一句话概括(20-50字)",
  "content": "完整内容(100-300字)",
  "commands": "相关命令或代码(无则空字符串)",
  "related": ["相关知识点标题(无则空数组)"]
}}]
```

只返回 JSON。"""


def parse_extraction_result(raw: str) -> list[dict]:
    # 尝试 ```json ... ``` 代码块
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", raw, re.DOTALL)
    json_str = match.group(1) if match else raw.strip()
    try:
        result = json.loads(json_str)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        match = re.search(r"\[.*\]", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return []


def extract_knowledge(messages: list[str]) -> list[dict]:
    import httpx

    schema = load_schema()
    prompt = build_extraction_prompt(schema, messages)

    base_url = os.environ.get("ANTHROPIC_BASE_URL", "").rstrip("/")
    api_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    model = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
    # 第三方 API（如 LongCat）的模型名可能不带 [1m] 后缀
    model = re.sub(r"\[.*?\]", "", model)

    # 直接用 httpx 发请求，兼容第三方 API 的认证方式（Authorization: Bearer）
    # Anthropic SDK 默认用 X-Api-Key header，部分第三方 API 不支持
    resp = httpx.post(
        f"{base_url}/v1/messages",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        json={
            "model": model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    raw = data["content"][0]["text"]
    return parse_extraction_result(raw)
