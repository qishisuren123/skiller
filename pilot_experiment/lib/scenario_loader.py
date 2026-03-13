"""
场景加载器：从 scenarios/ 目录加载场景到统一 dict 格式。
提供与旧 SCENARIOS dict 兼容的接口。
"""
import yaml
from pathlib import Path
from typing import Optional


def load_scenario(scenario_dir: Path) -> dict:
    """
    加载单个场景目录，返回统一格式的 dict。

    参数:
        scenario_dir: 场景目录路径（如 scenarios/S001_neuro_metadata/）

    返回:
        {
            "id": "S001_neuro_metadata",
            "name": "neuro_metadata",
            "task": "...",           # task.md 内容
            "test": "...",           # test_script.py 内容
            "difficulty": "easy",
            "domain": "neuroscience",
            "source": "real",        # real / synthetic
            "tags": [...],
            "required_packages": [...],
            "dir": Path,
        }
    """
    meta_path = scenario_dir / "scenario.yaml"
    task_path = scenario_dir / "task.md"
    test_path = scenario_dir / "test_script.py"

    if not meta_path.exists():
        raise FileNotFoundError(f"缺少 scenario.yaml: {scenario_dir}")
    if not task_path.exists():
        raise FileNotFoundError(f"缺少 task.md: {scenario_dir}")
    if not test_path.exists():
        raise FileNotFoundError(f"缺少 test_script.py: {scenario_dir}")

    meta = yaml.safe_load(meta_path.read_text())
    return {
        "id": meta["id"],
        "name": meta.get("name", scenario_dir.name),
        "task": task_path.read_text(),
        "test": test_path.read_text(),
        "difficulty": meta.get("difficulty", "medium"),
        "domain": meta.get("domain", "unknown"),
        "source": meta.get("source", "real"),
        "tags": meta.get("tags", []),
        "required_packages": meta.get("required_packages", []),
        "csv_row": meta.get("csv_row", None),
        "dir": scenario_dir,
    }


def load_all_scenarios(scenarios_dir: Optional[Path] = None) -> dict:
    """
    加载所有场景，返回 {scenario_key: scenario_dict}。
    与旧 SCENARIOS dict 格式兼容。

    参数:
        scenarios_dir: scenarios/ 目录路径，默认用 config 中的路径
    """
    if scenarios_dir is None:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from config import SCENARIOS_DIR
        scenarios_dir = SCENARIOS_DIR

    scenarios = {}
    for d in sorted(scenarios_dir.glob("S???_*")):
        if not d.is_dir():
            continue
        try:
            s = load_scenario(d)
            scenarios[s["id"]] = s
        except (FileNotFoundError, yaml.YAMLError, KeyError) as e:
            print(f"  WARNING: 跳过 {d.name}: {e}")
    return scenarios


def filter_scenarios(scenarios: dict,
                     difficulty: Optional[str] = None,
                     domain: Optional[str] = None,
                     source: Optional[str] = None,
                     tags: Optional[list[str]] = None) -> dict:
    """按条件筛选场景"""
    result = {}
    for key, s in scenarios.items():
        if difficulty and s["difficulty"] != difficulty:
            continue
        if domain and s["domain"] != domain:
            continue
        if source and s["source"] != source:
            continue
        if tags and not any(t in s.get("tags", []) for t in tags):
            continue
        result[key] = s
    return result


def stratified_sample(scenarios: dict, n: int, seed: int = 42) -> list[str]:
    """
    分层抽样：按难度和来源均衡抽取场景。
    返回 scenario_key 列表。
    """
    import random
    random.seed(seed)

    # 按 (difficulty, source) 分组
    groups = {}
    for key, s in scenarios.items():
        g = (s["difficulty"], s["source"])
        groups.setdefault(g, []).append(key)

    # 按比例抽样
    sampled = []
    total = sum(len(v) for v in groups.values())
    for g, keys in sorted(groups.items()):
        n_group = max(1, round(n * len(keys) / total))
        random.shuffle(keys)
        sampled.extend(keys[:n_group])

    # 如果多了就裁剪，少了就补
    random.shuffle(sampled)
    if len(sampled) > n:
        sampled = sampled[:n]
    elif len(sampled) < n:
        remaining = [k for k in scenarios if k not in sampled]
        random.shuffle(remaining)
        sampled.extend(remaining[:n - len(sampled)])

    return sorted(sampled)
