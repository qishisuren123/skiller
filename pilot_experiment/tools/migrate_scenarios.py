#!/usr/bin/env python3
"""
迁移脚本：将 scenarios_v2.py + scenarios_extended.py 中的 30 个场景
提取到独立目录 scenarios/S001_*/ ~ scenarios/S030_*/

每个目录包含:
- scenario.yaml: 元数据
- task.md: 任务描述
- test_script.py: 测试脚本
"""
import sys, os, re, yaml
from pathlib import Path

# 项目根目录
ROOT = Path("pilot_experiment")
sys.path.insert(0, str(ROOT / "scripts"))

# 导入所有场景
from scenarios_v2 import SCENARIOS
from scenarios_extended import SCENARIOS_EXTENDED
SCENARIOS.update(SCENARIOS_EXTENDED)

# 场景 ID → 新目录名映射（S01 → S001）
SCENARIO_MAPPING = {
    # S01-S10 (from scenarios_v2.py)
    "S01_neuro_metadata":    "S001_neuro_metadata",
    "S02_spike_behavior":    "S002_spike_behavior",
    "S03_spatial_tx":        "S003_spatial_tx",
    "S04_satellite":         "S004_satellite",
    "S05_protein_parse":     "S005_protein_parse",
    "S06_gene_expression":   "S006_gene_expression",
    "S07_data_viz":          "S007_data_viz",
    "S08_materials_qa":      "S008_materials_qa",
    "S09_earth_obs":         "S009_earth_obs",
    "S10_multimodal":        "S010_multimodal",
    # S11-S30 (from scenarios_extended.py)
    "S11_particle_physics":  "S011_particle_physics",
    "S12_uv_spectroscopy":   "S012_uv_spectroscopy",
    "S13_biodiversity":      "S013_biodiversity",
    "S14_clinical_lab":      "S014_clinical_lab",
    "S15_light_curves":      "S015_light_curves",
    "S16_fastq_qc":          "S016_fastq_qc",
    "S17_ctd_ocean":         "S017_ctd_ocean",
    "S18_radiosonde":        "S018_radiosonde",
    "S19_eeg_filtering":     "S019_eeg_filtering",
    "S20_survey_analysis":   "S020_survey_analysis",
    "S21_air_quality":       "S021_air_quality",
    "S22_well_log":          "S022_well_log",
    "S23_epidemic_curve":    "S023_epidemic_curve",
    "S24_xrd_peaks":         "S024_xrd_peaks",
    "S25_citation_graph":    "S025_citation_graph",
    "S26_earthquake_catalog":"S026_earthquake_catalog",
    "S27_crop_features":     "S027_crop_features",
    "S28_audio_features":    "S028_audio_features",
    "S29_flood_frequency":   "S029_flood_frequency",
    "S30_fossil_morpho":     "S030_fossil_morpho",
}

# 需要的包（从测试脚本 import 推断）
COMMON_PACKAGES = ["numpy", "subprocess", "tempfile", "json", "os", "sys"]

def infer_packages(test_code: str) -> list[str]:
    """从测试代码推断需要的包"""
    pkgs = set()
    for line in test_code.split("\n"):
        line = line.strip()
        if line.startswith("import "):
            for mod in line.replace("import ", "").split(","):
                mod = mod.strip().split(" as ")[0].split(".")[0]
                if mod and mod not in ("sys", "os", "subprocess", "tempfile", "json", "re", "io", "math", "struct", "base64"):
                    pkgs.add(mod)
        elif line.startswith("from "):
            mod = line.split("from ")[1].split(" import")[0].strip().split(".")[0]
            if mod and mod not in ("sys", "os", "subprocess", "tempfile", "json", "re", "io", "math", "struct", "base64"):
                pkgs.add(mod)
    return sorted(pkgs)


def migrate_scenario(old_key: str, new_id: str, data: dict):
    """迁移单个场景到新目录"""
    scenario_dir = ROOT / "scenarios" / new_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    # 1. scenario.yaml
    # 从 old_key 提取名称（去掉 S01_ 前缀）
    name = old_key.split("_", 1)[1] if "_" in old_key else old_key
    source_info = data.get("source", "unknown")
    # 判断是 real 还是 synthetic
    is_real = source_info != "synthetic" and not source_info.startswith("synthetic")
    source_type = "real" if is_real else "synthetic"

    required_packages = infer_packages(data["test"])

    meta = {
        "id": new_id,
        "name": name,
        "domain": data.get("domain", "unknown"),
        "difficulty": data.get("difficulty", "medium"),
        "source": source_type,
        "csv_row": source_info if is_real else None,
        "tags": [data.get("domain", "unknown"), data.get("difficulty", "medium")],
        "required_packages": required_packages,
    }
    yaml_path = scenario_dir / "scenario.yaml"
    yaml_path.write_text(yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False))

    # 2. task.md
    task_path = scenario_dir / "task.md"
    task_path.write_text(data["task"].strip() + "\n")

    # 3. test_script.py
    test_path = scenario_dir / "test_script.py"
    test_path.write_text(data["test"].strip() + "\n")

    print(f"  ✓ {new_id} ({data['domain']}, {data['difficulty']}, {source_type})")


def main():
    print(f"迁移 {len(SCENARIO_MAPPING)} 个场景...")
    print(f"目标目录: {ROOT / 'scenarios'}")
    print()

    migrated = 0
    for old_key, new_id in sorted(SCENARIO_MAPPING.items(), key=lambda x: x[1]):
        if old_key not in SCENARIOS:
            print(f"  ✗ {old_key} 未找到，跳过")
            continue
        migrate_scenario(old_key, new_id, SCENARIOS[old_key])
        migrated += 1

    print(f"\n完成！迁移了 {migrated}/{len(SCENARIO_MAPPING)} 个场景")

    # 验证
    print("\n验证迁移结果:")
    scenarios_dir = ROOT / "scenarios"
    dirs = sorted(d for d in scenarios_dir.glob("S???_*") if d.is_dir())
    print(f"  总目录数: {len(dirs)}")
    for d in dirs:
        has_yaml = (d / "scenario.yaml").exists()
        has_task = (d / "task.md").exists()
        has_test = (d / "test_script.py").exists()
        status = "✓" if (has_yaml and has_task and has_test) else "✗"
        print(f"  {status} {d.name}: yaml={has_yaml}, task={has_task}, test={has_test}")


if __name__ == "__main__":
    main()
