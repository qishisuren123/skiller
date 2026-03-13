"""调用 LLM API 生成代码的 runner"""
import json
import re
import anthropic
from pathlib import Path
from config import API_KEY, BASE_URL, MODELS, RAW_DIR, log_cost


def build_prompt(task_desc: str, skill_content: str | None = None) -> list[dict]:
    """构建 messages，skill 作为 system prompt 注入"""
    system = ""
    if skill_content:
        system = (
            "You are given the following skill document to guide your work. "
            "Follow its instructions, workflow, and pitfalls carefully.\n\n"
            f"<skill>\n{skill_content}\n</skill>"
        )
    messages = [{"role": "user", "content": task_desc}]
    return system, messages


def call_model(model_key: str, task_desc: str, skill_content: str | None,
               scenario: str, condition: str, max_tokens: int = 8192) -> dict:
    """调用模型，返回生成的文本和 metadata"""
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)
    system, messages = build_prompt(task_desc, skill_content)

    kwargs = {
        "model": MODELS[model_key],
        "max_tokens": max_tokens,
        "temperature": 0,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    resp = client.messages.create(**kwargs)

    text = resp.content[0].text
    cost = log_cost(model_key, resp.usage.input_tokens, resp.usage.output_tokens,
                    scenario, condition)

    result = {
        "model": model_key,
        "scenario": scenario,
        "condition": condition,
        "input_tokens": resp.usage.input_tokens,
        "output_tokens": resp.usage.output_tokens,
        "cost_usd": cost,
        "response": text,
        "stop_reason": resp.stop_reason,
    }

    # 保存原始结果
    raw_file = RAW_DIR / f"{scenario}__{condition}__{model_key}.json"
    raw_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))

    return result


def extract_python_code(text: str) -> str:
    """从 LLM 回复中提取最长的 python 代码块"""
    blocks = re.findall(r"```python\s*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        # 尝试无语言标记的代码块
        blocks = re.findall(r"```\s*\n(.*?)```", text, re.DOTALL)
    if not blocks:
        return ""
    # 返回最长的代码块（通常是主脚本）
    return max(blocks, key=len).strip()
