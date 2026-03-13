"""统一 API 调用客户端：call_model() + extract_python_code()"""
import json
import os
import re
import time
from pathlib import Path

# 从根目录 config 导入
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import API_KEY, BASE_URL, MODELS, log_cost, RAW_DIR


def call_model(model_key: str, task_desc: str, skill_content: str | None,
               scenario: str, condition: str, max_tokens: int = 8192,
               temperature: float = 0.0, run_id: int = 0) -> dict:
    """
    统一 API 调用，支持 temperature 和多次运行。
    skill_content 可以是序列化后的 skill 包文本（由 skill_injector 生成）。
    """
    import anthropic
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    system = ""
    if skill_content:
        system = ("You are given the following skill package to guide your work. "
                  "Follow its instructions carefully.\n\n"
                  f"<skill-package>\n{skill_content}\n</skill-package>")

    # 记录 skill token 数（粗略按空格分词估算）
    skill_token_count = len(skill_content.split()) if skill_content else 0

    messages = [{"role": "user", "content": task_desc}]
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

    # 文件名包含 run_id（多次运行时区分）
    suffix = f"_run{run_id}" if run_id > 0 else ""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    raw_file = RAW_DIR / f"{scenario}__{condition}__{model_key}{suffix}.json"

    result = {
        "model": model_key,
        "scenario": scenario,
        "condition": condition,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cost_usd": cost,
        "response": text,
        "stop_reason": resp.stop_reason,
        "skill_token_count": skill_token_count,
        "temperature": temperature,
        "run_id": run_id,
    }
    raw_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def extract_python_code(text: str) -> str:
    """从 LLM 回复中提取 Python 代码块（取最长的一个）"""
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        blocks = re.findall(r"```\s*\n(.*?)```", text, re.DOTALL)
    return max(blocks, key=len).strip() if blocks else ""
