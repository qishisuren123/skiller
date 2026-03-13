"""
LLM-as-Judge 模块：用 Haiku 对生成代码评 4 个维度 (1-5 分)
- Correctness: 代码逻辑是否正确
- Robustness: 错误处理和边界情况
- Style: 代码风格和可读性
- Skill_adherence: 是否遵循了 skill 文档的建议（仅当有 skill 时评分）

每次调用约 $0.002 (Haiku)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config import API_KEY, BASE_URL, MODELS, log_cost
import anthropic

JUDGE_PROMPT = """You are a code quality judge for scientific data processing scripts.

Rate the following Python code on these dimensions (1-5 scale each):

1. **Correctness** (1-5): Does the code correctly implement the task requirements?
   - 1: Completely wrong or doesn't run
   - 3: Partially correct, misses some requirements
   - 5: Fully correct implementation

2. **Robustness** (1-5): How well does the code handle errors and edge cases?
   - 1: No error handling, crashes on bad input
   - 3: Basic try/except, handles common cases
   - 5: Comprehensive error handling, graceful degradation

3. **Style** (1-5): Code readability, organization, and Pythonic patterns?
   - 1: Unreadable, no structure
   - 3: Readable but could be improved
   - 5: Clean, well-organized, follows PEP 8

4. **Skill_adherence** (1-5): Does the code follow the skill document's guidance?
   - 1: Completely ignores skill advice
   - 3: Partially follows skill
   - 5: Closely follows all skill recommendations
   - N/A: No skill was provided (output 0)

## Task Description:
{task}

## Skill Document (if any):
{skill}

## Generated Code:
```python
{code}
```

## Test Results:
Pass rate: {pass_rate}
Failed tests: {failed_tests}

Respond ONLY in this exact JSON format (no other text):
{{"correctness": <int>, "robustness": <int>, "style": <int>, "skill_adherence": <int>, "brief_reason": "<1 sentence>"}}
"""


def judge_code(code: str, task: str, skill: str | None,
               pass_rate: float, failed_tests: list[str],
               scenario: str = "unknown") -> dict:
    """
    用 Haiku 评判代码质量，返回 4 维度分数。
    """
    client = anthropic.Anthropic(api_key=API_KEY, base_url=BASE_URL)

    skill_text = skill if skill else "(No skill document was provided)"
    failed_str = ", ".join(failed_tests[:10]) if failed_tests else "None"

    prompt = JUDGE_PROMPT.format(
        task=task[:2000],
        skill=skill_text[:3000],
        code=code[:4000],
        pass_rate=f"{pass_rate:.0%}",
        failed_tests=failed_str,
    )

    try:
        resp = client.messages.create(
            model=MODELS["haiku"],
            max_tokens=256,
            temperature=0,
            messages=[{"role": "user", "content": prompt}],
        )
        text = resp.content[0].text.strip()
        cost = log_cost("haiku", resp.usage.input_tokens, resp.usage.output_tokens,
                        scenario, "llm_judge")

        # 解析 JSON
        # 去掉可能的 markdown 包裹
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0]
        scores = json.loads(text)
        scores["cost_usd"] = cost
        return scores

    except Exception as e:
        return {
            "correctness": 0, "robustness": 0, "style": 0, "skill_adherence": 0,
            "brief_reason": f"Judge error: {str(e)[:100]}",
            "cost_usd": 0,
        }


def judge_batch(results_dir: Path, scenarios: dict, skill_cache_dir: Path,
                output_path: Path) -> list[dict]:
    """
    批量评判 results/raw/ 下所有结果。
    """
    import re
    raw_dir = results_dir / "raw"
    all_scores = []

    for f in sorted(raw_dir.glob("*.json")):
        data = json.loads(f.read_text())
        scenario_key = data.get("scenario", "")
        condition = data.get("condition", "")
        model = data.get("model", "")
        response = data.get("response", "")

        if not response:
            continue

        # 提取代码
        blocks = re.findall(r"```python\s*\n(.*?)```", response, re.DOTALL)
        if not blocks:
            blocks = re.findall(r"```\s*\n(.*?)```", response, re.DOTALL)
        code = max(blocks, key=len).strip() if blocks else ""
        if not code:
            continue

        # 获取 task 描述
        task = scenarios.get(scenario_key, {}).get("task", "Unknown task")

        # 获取 skill（如果是 exact_skill 条件）
        skill = None
        if "skill" in condition and "no_skill" not in condition:
            # 尝试找对应的 skill cache
            skill_file = skill_cache_dir / f"{scenario_key}__sonnet.md"
            if skill_file.exists():
                skill = skill_file.read_text()

        # 获取测试结果
        eval_data = data.get("eval", {})
        pass_rate = eval_data.get("pass_rate", 0)
        failed = [d["test"] for d in eval_data.get("details", []) if not d.get("pass")]

        scores = judge_code(code, task, skill, pass_rate, failed, scenario_key)
        scores["file"] = f.name
        scores["scenario"] = scenario_key
        scores["condition"] = condition
        scores["model"] = model
        all_scores.append(scores)

        print(f"  Judged {f.name}: C={scores['correctness']} R={scores['robustness']} "
              f"S={scores['style']} A={scores['skill_adherence']} ${scores['cost_usd']:.4f}")

    # 保存结果
    output_path.write_text(json.dumps(all_scores, indent=2, ensure_ascii=False))
    total_cost = sum(s["cost_usd"] for s in all_scores)
    print(f"\nJudge complete: {len(all_scores)} evaluations, total ${total_cost:.4f}")
    return all_scores


if __name__ == "__main__":
    from config import RESULTS_DIR
    from scenarios_v2 import SCENARIOS

    SKILL_CACHE = RESULTS_DIR / "skill_cache"
    output = RESULTS_DIR / "llm_judge_scores.json"
    judge_batch(RESULTS_DIR, SCENARIOS, SKILL_CACHE, output)
