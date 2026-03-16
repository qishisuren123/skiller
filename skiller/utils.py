#!/usr/bin/env python3
"""
工具函数：API 调用、成本追踪、文件解析等。
"""
import json
import time
import re
import os
from pathlib import Path

# API 配置 — 从环境变量读取
API_KEY = os.environ.get("SKILLER_API_KEY", "")
BASE_URL = os.environ.get("SKILLER_BASE_URL", "http://localhost:3888")

# 模型列表
MODELS = {
    "haiku": "claude-haiku-4-5-20251001",
    "sonnet": "claude-sonnet-4-20250514",
    "opus": "claude-opus-4-20250514",
    "gpt4o": "gpt-4o",
    "gpt4o_mini": "gpt-4o-mini",
    "gpt41": "gpt-4.1",
    "gpt41_mini": "gpt-4.1-mini",
    "gemini_pro": "gemini-2.5-pro",
    "gemini_flash": "gemini-2.5-flash",
}

# 成本估算（美元/百万 token）
COST_PER_M = {
    "haiku":        {"input": 0.80,  "output": 4.00},
    "sonnet":       {"input": 3.00,  "output": 15.00},
    "opus":         {"input": 15.00, "output": 75.00},
    "gpt4o":        {"input": 2.50,  "output": 10.00},
    "gpt4o_mini":   {"input": 0.15,  "output": 0.60},
    "gpt41":        {"input": 2.00,  "output": 8.00},
    "gpt41_mini":   {"input": 0.40,  "output": 1.60},
    "gemini_pro":   {"input": 1.25,  "output": 10.00},
    "gemini_flash": {"input": 0.15,  "output": 0.60},
}

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
COST_LOG = PROJECT_ROOT / "data" / "cost_log.jsonl"


def log_cost(model_key: str, input_tokens: int, output_tokens: int,
             scenario: str, condition: str) -> float:
    """记录 API 调用成本"""
    rates = COST_PER_M.get(model_key, {"input": 0, "output": 0})
    cost = (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000
    entry = {
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_key,
        "scenario": scenario,
        "condition": condition,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost_usd": round(cost, 6),
    }
    COST_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(COST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return cost


def total_cost() -> float:
    """读取总花费"""
    if not COST_LOG.exists():
        return 0.0
    total = 0.0
    for line in COST_LOG.read_text().strip().split("\n"):
        if line:
            total += json.loads(line)["cost_usd"]
    return round(total, 4)


def call_llm(model_key: str, messages: list, system: str = "",
             max_tokens: int = 8192, temperature: float = 0.3,
             scenario: str = "", condition: str = "") -> dict:
    """统一 LLM 调用（通过 Anthropic SDK，兼容 OpenAI 格式的 gateway）"""
    import anthropic
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)

    kwargs = {
        "model": MODELS[model_key],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    resp = client.messages.create(**kwargs)
    text = resp.content[0].text
    cost = log_cost(model_key, resp.usage.input_tokens, resp.usage.output_tokens,
                    scenario, condition)

    return {
        "text": text,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cost_usd": cost,
        "model": model_key,
    }


def extract_python_code(text: str) -> str:
    """从 LLM 回复中提取最长的 Python 代码块"""
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        blocks = re.findall(r"```\s*\n(.*?)```", text, re.DOTALL)
    return max(blocks, key=len).strip() if blocks else ""


def parse_skill_output(text: str) -> dict:
    """解析 LLM 输出为 skill 包文件字典"""
    files = {}
    patterns = {
        "SKILL.md": r"```skill_md\s*\n(.*?)```",
        "scripts/main.py": r"```script_main\s*\n(.*?)```",
        "scripts/requirements.txt": r"```script_requirements\s*\n(.*?)```",
        "references/workflow.md": r"```reference_workflow\s*\n(.*?)```",
        "references/pitfalls.md": r"```reference_pitfalls\s*\n(.*?)```",
        "assets/example_output.md": r"```asset_example_output\s*\n(.*?)```",
    }
    for filename, pattern in patterns.items():
        m = re.search(pattern, text, re.DOTALL)
        if m:
            files[filename] = m.group(1).strip()
    return files


def save_skill_package(skill_dir: Path, files: dict):
    """保存 skill 包到目录"""
    for subdir in ["scripts", "references", "assets"]:
        (skill_dir / subdir).mkdir(parents=True, exist_ok=True)

    for rel_path, content in files.items():
        fp = skill_dir / rel_path
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content + "\n", encoding="utf-8")


def serialize_skill_package(skill_dir: Path, level: str = "L4_full") -> str:
    """将 skill 目录序列化为单个字符串"""
    LEVELS = {
        "L0_none":         {"skill_md": False, "scripts": False, "references": False, "assets": False},
        "L1_skill_md":     {"skill_md": True,  "scripts": False, "references": False, "assets": False},
        "L2_plus_scripts": {"skill_md": True,  "scripts": True,  "references": False, "assets": False},
        "L3_no_assets":    {"skill_md": True,  "scripts": True,  "references": True,  "assets": False},
        "L4_full":         {"skill_md": True,  "scripts": True,  "references": True,  "assets": True},
    }
    if level == "L0_none":
        return ""
    config = LEVELS[level]
    parts = []

    if config["skill_md"]:
        p = skill_dir / "SKILL.md"
        if p.exists():
            parts.append(f'<file path="SKILL.md">\n{p.read_text()}\n</file>')
        else:
            return ""

    for dirname, key in [("scripts", "scripts"), ("references", "references"), ("assets", "assets")]:
        if config[key]:
            d = skill_dir / dirname
            if d.exists():
                for f in sorted(d.glob("*")):
                    if f.is_file():
                        try:
                            content = f.read_text(encoding="utf-8")
                        except UnicodeDecodeError:
                            content = f"[binary file: {f.name}]"
                        parts.append(f'<file path="{dirname}/{f.name}">\n{content}\n</file>')

    return "\n\n".join(parts)


def estimate_tokens(text: str) -> int:
    """粗略估算 token 数"""
    if not text:
        return 0
    return int(len(text.split()) * 1.3)
