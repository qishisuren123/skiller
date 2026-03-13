"""
Skill Stripper: SKILL.md 内部的子级裁剪。

在 RQ1 中，除了跨文件的 5 级完整度（由 skill_injector 控制），
还需要在 SKILL.md 内部做更细粒度的裁剪实验：
- overview_only: 仅保留第一个 section（概述）
- no_pitfalls: 去掉 pitfalls/warnings 段
- no_code: 去掉所有代码块
- text_only: 去掉所有代码块（同上，语义别名）
- code_only: 仅保留代码块
- pitfalls_only: 仅保留 pitfalls 段
- workflow_only: 仅保留 workflow/steps 段
- first_half / second_half: 位置切割
- length_Npct: 截断到 N% 长度
"""
import re
from pathlib import Path


def strip_skill(skill_text: str, mode: str) -> str:
    """
    裁剪 SKILL.md 文本到指定子级。

    参数:
        skill_text: SKILL.md 的原始文本
        mode: 裁剪模式

    返回:
        裁剪后的文本
    """
    if not skill_text:
        return ""

    if mode == "full":
        return skill_text

    elif mode == "overview_only":
        sections = re.split(r'\n(?=## )', skill_text)
        return sections[0][:500] if sections else skill_text[:500]

    elif mode in ("no_code", "text_only"):
        return re.sub(r"```(?:python)?\s*\n.*?```", "", skill_text, flags=re.DOTALL).strip()

    elif mode == "code_only":
        blocks = re.findall(r"```(?:python)?\s*\n(.*?)```", skill_text, re.DOTALL)
        return "\n\n".join(f"```python\n{b}\n```" for b in blocks) if blocks else ""

    elif mode == "pitfalls_only":
        sections = re.split(r'\n(?=## )', skill_text)
        pitfall_kw = ["pitfall", "common", "warning", "issue", "error", "gotcha", "caveat"]
        pitfall_sections = [s for s in sections
                           if any(kw in s.lower() for kw in pitfall_kw)]
        return "\n\n".join(pitfall_sections) if pitfall_sections else skill_text[:500]

    elif mode == "workflow_only":
        sections = re.split(r'\n(?=## )', skill_text)
        workflow_kw = ["workflow", "step", "procedure", "process", "approach", "algorithm"]
        workflow_sections = [s for s in sections
                            if any(kw in s.lower() for kw in workflow_kw)]
        return "\n\n".join(workflow_sections) if workflow_sections else skill_text[:500]

    elif mode == "no_pitfalls":
        sections = re.split(r'\n(?=## )', skill_text)
        pitfall_kw = ["pitfall", "common", "warning", "issue", "error", "gotcha", "caveat"]
        kept = [s for s in sections
                if not any(kw in s.lower() for kw in pitfall_kw)]
        return "\n\n".join(kept).strip()

    elif mode == "first_half":
        return skill_text[:len(skill_text) // 2]

    elif mode == "second_half":
        return skill_text[len(skill_text) // 2:]

    elif mode.startswith("length_") and mode.endswith("pct"):
        # 格式: length_25pct, length_50pct, length_75pct
        pct_str = mode.replace("length_", "").replace("pct", "")
        try:
            pct = int(pct_str) / 100.0
        except ValueError:
            return skill_text
        return skill_text[:int(len(skill_text) * pct)]

    else:
        raise ValueError(f"未知裁剪模式: {mode}，可选: full, overview_only, no_code, text_only, "
                         f"code_only, pitfalls_only, workflow_only, no_pitfalls, "
                         f"first_half, second_half, length_Npct")


# 所有可用的裁剪模式列表
STRIP_MODES = [
    "full", "overview_only", "text_only", "code_only",
    "pitfalls_only", "workflow_only", "no_pitfalls",
    "first_half", "second_half",
    "length_25pct", "length_50pct", "length_75pct",
]
