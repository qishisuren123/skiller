"""
Skill Injector: 将多文件 skill 包序列化为单个文本，注入 LLM prompt。

完整度级别 (RQ1 实验变量):
- L0_none:        无 skill
- L1_skill_md:    仅 SKILL.md
- L2_plus_scripts: SKILL.md + scripts/
- L3_no_assets:   SKILL.md + scripts/ + references/
- L4_full:        完整包（含 assets/）
"""
from pathlib import Path

# 完整度级别名称到配置的映射
COMPLETENESS_LEVELS = {
    "L0_none":         {"skill_md": False, "scripts": False, "references": False, "assets": False},
    "L1_skill_md":     {"skill_md": True,  "scripts": False, "references": False, "assets": False},
    "L2_plus_scripts": {"skill_md": True,  "scripts": True,  "references": False, "assets": False},
    "L3_no_assets":    {"skill_md": True,  "scripts": True,  "references": True,  "assets": False},
    "L4_full":         {"skill_md": True,  "scripts": True,  "references": True,  "assets": True},
}


def _read_text_safe(path: Path) -> str:
    """安全读取文本文件，跳过二进制文件"""
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, ValueError):
        return f"[binary file: {path.name}, {path.stat().st_size} bytes]"


def serialize_skill_package(skill_dir: Path, level: str = "L4_full") -> str:
    """
    将 skill 目录序列化为单个字符串，用 <file> 标签分隔。

    参数:
        skill_dir: skill 包目录路径（包含 SKILL.md, scripts/, references/, assets/）
        level: 完整度级别 (L0_none ~ L4_full)

    返回:
        序列化后的文本，可直接放入 system prompt
    """
    if level == "L0_none":
        return ""

    config = COMPLETENESS_LEVELS.get(level)
    if config is None:
        raise ValueError(f"未知完整度级别: {level}，可选: {list(COMPLETENESS_LEVELS.keys())}")

    parts = []

    # SKILL.md（核心文件，所有非 L0 级别都包含）
    if config["skill_md"]:
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            parts.append(f'<file path="SKILL.md">\n{skill_md.read_text()}\n</file>')
        else:
            return ""  # 没有 SKILL.md 则整个 skill 无效

    # scripts/ 目录
    if config["scripts"]:
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            for f in sorted(scripts_dir.glob("*")):
                if f.is_file():
                    content = _read_text_safe(f)
                    parts.append(f'<file path="scripts/{f.name}">\n{content}\n</file>')

    # references/ 目录
    if config["references"]:
        refs_dir = skill_dir / "references"
        if refs_dir.exists():
            for f in sorted(refs_dir.glob("*")):
                if f.is_file():
                    content = _read_text_safe(f)
                    parts.append(f'<file path="references/{f.name}">\n{content}\n</file>')

    # assets/ 目录
    if config["assets"]:
        assets_dir = skill_dir / "assets"
        if assets_dir.exists():
            for f in sorted(assets_dir.glob("*")):
                if f.is_file():
                    content = _read_text_safe(f)
                    parts.append(f'<file path="assets/{f.name}">\n{content}\n</file>')

    return "\n\n".join(parts)


def build_system_prompt(serialized_skill: str) -> str:
    """将序列化的 skill 包装为 system prompt"""
    if not serialized_skill:
        return ""
    return (
        "You are given the following skill package to guide your work. "
        "Follow its instructions carefully.\n\n"
        f"<skill-package>\n{serialized_skill}\n</skill-package>"
    )


def estimate_tokens(serialized_skill: str) -> int:
    """粗略估算 skill 的 token 数（按空格分词 × 1.3）"""
    if not serialized_skill:
        return 0
    return int(len(serialized_skill.split()) * 1.3)
