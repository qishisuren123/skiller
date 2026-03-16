#!/usr/bin/env python3
"""
Step 1: 从 pilot_experiment 的 100 个场景中筛选 50 个，覆盖 10+ 领域。
按领域分组，每组选 4-6 个（取决于可用数量），输出 selected_scenarios.json。
"""
import json
import random
import yaml
from pathlib import Path
from collections import defaultdict

SCENARIOS_DIR = Path("/mnt/shared-storage-user/renyiming/skill_v4_restored/pilot_experiment/scenarios")
OUTPUT_PATH = Path("/mnt/shared-storage-user/renyiming/skiller/selected_scenarios.json")

# 领域合并映射（把相近的领域合并到大类）
DOMAIN_MERGE = {
    "neuroscience": "neuroscience",
    "life_science": "biology",
    "genomics": "biology",
    "protein_structure": "biology",
    "ecology": "ecology",
    "medical": "medical",
    "epidemiology": "medical",
    "astronomy": "astronomy",
    "physics": "physics",
    "chemistry": "chemistry",
    "materials_science": "materials",
    "materials": "materials",
    "earth_science": "earth_science",
    "geology": "earth_science",
    "seismology": "earth_science",
    "oceanography": "oceanography",
    "atmospheric_science": "atmospheric",
    "atmospheric": "atmospheric",
    "hydrology": "earth_science",
    "environmental_science": "environmental",
    "agricultural_science": "environmental",
    "signal_processing": "engineering",
    "psychoacoustics": "engineering",
    "social_science": "social_science",
    "network_science": "social_science",
    "paleontology": "ecology",
}

# 每个大领域的目标数量
TARGET_PER_DOMAIN = {
    "earth_science": 5,
    "biology": 6,
    "physics": 4,
    "chemistry": 4,
    "astronomy": 5,
    "engineering": 4,
    "environmental": 4,
    "medical": 4,
    "social_science": 4,
    "neuroscience": 3,
    "ecology": 4,
    "oceanography": 4,
    "atmospheric": 4,
    "materials": 4,
}

# 领域展示名
DOMAIN_DISPLAY = {
    "earth_science": "Earth Science",
    "biology": "Biology / Genomics",
    "physics": "Physics",
    "chemistry": "Chemistry",
    "astronomy": "Astronomy",
    "engineering": "Signal Processing / Engineering",
    "environmental": "Environmental Science",
    "medical": "Medical / Epidemiology",
    "social_science": "Social Science / Networks",
    "neuroscience": "Neuroscience",
    "ecology": "Ecology / Biodiversity",
    "oceanography": "Oceanography",
    "atmospheric": "Atmospheric Science",
    "materials": "Materials Science",
}


def load_scenarios():
    """加载所有场景元数据"""
    scenarios = []
    for d in sorted(SCENARIOS_DIR.glob("S???_*")):
        if not d.is_dir():
            continue
        meta_path = d / "scenario.yaml"
        task_path = d / "task.md"
        test_path = d / "test_script.py"
        if not all(p.exists() for p in [meta_path, task_path, test_path]):
            continue
        meta = yaml.safe_load(meta_path.read_text())
        scenarios.append({
            "id": meta["id"],
            "name": meta.get("name", d.name),
            "domain": meta.get("domain", "unknown"),
            "difficulty": meta.get("difficulty", "medium"),
            "source": meta.get("source", "synthetic"),
            "task_path": str(task_path),
            "test_path": str(test_path),
            "scenario_dir": str(d),
        })
    return scenarios


def select_scenarios(scenarios, target_total=50, seed=42):
    """按领域分层抽样"""
    random.seed(seed)

    # 按合并后的领域分组
    by_domain = defaultdict(list)
    for s in scenarios:
        merged = DOMAIN_MERGE.get(s["domain"], s["domain"])
        s["domain_group"] = merged
        by_domain[merged].append(s)

    print(f"总场景数: {len(scenarios)}")
    print(f"原始领域数: {len(set(s['domain'] for s in scenarios))}")
    print(f"合并后领域数: {len(by_domain)}")
    print()

    selected = []
    for domain, members in sorted(by_domain.items()):
        target = TARGET_PER_DOMAIN.get(domain, min(len(members), 4))
        target = min(target, len(members))

        # 优先选不同难度的
        by_diff = defaultdict(list)
        for s in members:
            by_diff[s["difficulty"]].append(s)

        chosen = []
        for diff in ["easy", "medium", "hard"]:
            if diff in by_diff and len(chosen) < target:
                pool = by_diff[diff]
                random.shuffle(pool)
                need = max(1, (target - len(chosen)) // (1 + (diff != "hard")))
                chosen.extend(pool[:need])

        # 补齐
        remaining = [s for s in members if s not in chosen]
        random.shuffle(remaining)
        while len(chosen) < target and remaining:
            chosen.append(remaining.pop(0))

        display = DOMAIN_DISPLAY.get(domain, domain)
        print(f"  {display:35s}: {len(chosen)}/{len(members)} selected")
        for s in chosen:
            print(f"    - {s['id']:30s} [{s['difficulty']:6s}] {s['domain']}")

        selected.extend(chosen)

    # 如果超过目标，修剪
    if len(selected) > target_total:
        random.shuffle(selected)
        selected = selected[:target_total]

    # 如果不够，从剩余中补
    if len(selected) < target_total:
        used_ids = {s["id"] for s in selected}
        remaining = [s for s in scenarios if s["id"] not in used_ids]
        random.shuffle(remaining)
        selected.extend(remaining[:target_total - len(selected)])

    return sorted(selected, key=lambda s: s["id"])


def main():
    scenarios = load_scenarios()
    selected = select_scenarios(scenarios, target_total=50)

    # 统计
    domains = set(s["domain_group"] for s in selected)
    print(f"\n{'='*60}")
    print(f"已选: {len(selected)} 个场景, 覆盖 {len(domains)} 个领域")
    print(f"领域: {', '.join(sorted(domains))}")

    # 输出
    output = {
        "total": len(selected),
        "n_domains": len(domains),
        "domains": sorted(domains),
        "scenarios": selected,
    }
    OUTPUT_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n已保存: {OUTPUT_PATH}")

    # 同时生成 requirements.csv
    import csv
    csv_path = OUTPUT_PATH.parent / "data" / "requirements.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["scenario_id", "name", "domain", "domain_group", "difficulty", "source"])
        for s in selected:
            writer.writerow([s["id"], s["name"], s["domain"], s["domain_group"],
                           s["difficulty"], s["source"]])
    print(f"已保存: {csv_path}")


if __name__ == "__main__":
    main()
