"""
场景注册表：自动发现所有 S???_* 目录并加载。
提供与旧 SCENARIOS dict 完全兼容的接口。
"""
from pathlib import Path

# 场景目录
SCENARIOS_DIR = Path(__file__).parent

def load_all_scenarios() -> dict:
    """
    加载所有场景，返回 {scenario_key: {task, test, difficulty, domain, ...}}。
    与旧 SCENARIOS dict 兼容。
    """
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from lib.scenario_loader import load_all_scenarios as _load
    return _load(SCENARIOS_DIR)


def list_scenario_ids() -> list[str]:
    """列出所有可用的场景 ID"""
    ids = []
    for d in sorted(SCENARIOS_DIR.glob("S???_*")):
        if d.is_dir() and (d / "scenario.yaml").exists():
            ids.append(d.name)
    return ids


def get_scenario_dir(scenario_id: str) -> Path:
    """根据 ID 获取场景目录路径"""
    # 支持完整 ID（S001_neuro_metadata）或数字（S001 / 1 / 001）
    if scenario_id.startswith("S") and "_" in scenario_id:
        d = SCENARIOS_DIR / scenario_id
        if d.exists():
            return d

    # 尝试匹配数字前缀
    prefix = scenario_id.lstrip("S").lstrip("0") or "0"
    for d in SCENARIOS_DIR.glob(f"S{int(prefix):03d}_*"):
        if d.is_dir():
            return d

    raise FileNotFoundError(f"找不到场景: {scenario_id}")
