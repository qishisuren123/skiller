#!/usr/bin/env python3
"""
grade_results.py: 自动化评分脚本
对每次运行生成的 meta.json 检查 7 项断言，输出通过率。

断言:
  A1: meta.json 是合法 JSON
  A2: 列出全部 8 个文件
  A3: HDF5 dataset 记录了 shape/dtype
  A4: v7.3 MAT 文件被正确识别
  A5: Subject 文件被通配符合并
  A6: 无未处理错误
  A7: 包含预期 key 名 (CellResp, CellXYZ, periods 等)
"""

import json
import os
import sys
from pathlib import Path


def check_a1_valid_json(meta_path: str) -> tuple[bool, str]:
    """A1: meta.json 是合法 JSON"""
    try:
        with open(meta_path) as f:
            json.load(f)
        return True, "Valid JSON"
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return False, f"Invalid: {e}"


def check_a2_all_files(meta: dict) -> tuple[bool, str]:
    """A2: 列出全部 8 个文件（或通过 total_files 确认）"""
    # 检查 summary.total_files
    total = meta.get("summary", {}).get("total_files", 0)
    if total == 8:
        return True, f"total_files={total}"

    # 也检查 files 列表（可能有合并导致条目数不同）
    files = meta.get("files", [])
    # 统计实际文件数（合并条目要算 count）
    actual = sum(f.get("count", 1) for f in files)
    if actual == 8:
        return True, f"actual_count={actual} (via merge counts)"

    return False, f"total_files={total}, actual_count={actual}, expected 8"


def check_a3_shape_dtype(meta: dict) -> tuple[bool, str]:
    """A3: HDF5 dataset 记录了 shape/dtype"""
    files = meta.get("files", [])
    for f in files:
        fmt = f.get("format", "")
        if "hdf5" in fmt.lower() and f.get("format", "") != "mat-v7.3-hdf5" and f.get("format", "") != "mat-v7.3 (hdf5)":
            # 这是一个 HDF5 文件
            datasets = f.get("datasets", [])
            for ds in datasets:
                shape = ds.get("shape")
                if shape and len(shape) > 0:
                    return True, f"Found shape {shape} in HDF5 dataset"
    # 也检查 format 为 hdf5 的文件
    for f in files:
        if f.get("format") == "hdf5":
            for ds in f.get("datasets", []):
                if ds.get("shape") and len(ds["shape"]) > 0:
                    return True, f"Found shape {ds['shape']}"
    return False, "No HDF5 dataset with non-empty shape found"


def check_a4_v73_detected(meta: dict) -> tuple[bool, str]:
    """A4: v7.3 MAT 文件被正确识别"""
    files = meta.get("files", [])
    for f in files:
        fmt = str(f.get("format", "")).lower()
        if "v7.3" in fmt or ("hdf5" in fmt and "mat" in str(f.get("path", "")).lower()):
            return True, f"Detected format: {f.get('format')}"
    # 也检查 summary 中的 format_counts/format_breakdown
    summary = meta.get("summary", {})
    for key in ("format_counts", "format_breakdown"):
        counts = summary.get(key, {})
        for k in counts:
            if "v7.3" in k.lower() or ("hdf5" in k.lower() and "mat" in k.lower()):
                return True, f"Detected in summary: {k}"
    return False, "No v7.3 format detected in any file entry"


def check_a5_wildcard_merge(meta: dict) -> tuple[bool, str]:
    """A5: Subject 文件被通配符合并（存在 merged: true 条目）"""
    files = meta.get("files", [])
    for f in files:
        if f.get("merged") is True:
            return True, f"Merged entry: {f.get('path', f.get('file', '?'))} (count={f.get('count')})"
    # 也检查 matched_count 字段
    for f in files:
        if f.get("matched_count", 0) > 1:
            return True, f"matched_count={f['matched_count']}"
    # 也检查 structure_consistent
    for f in files:
        if f.get("structure_consistent") is True:
            return True, f"structure_consistent entry found"
    return False, "No merged/wildcard entries found"


def check_a6_no_errors(meta: dict) -> tuple[bool, str]:
    """A6: 无未处理错误（summary.errors == 0）"""
    errors = meta.get("summary", {}).get("errors", -1)
    if errors == 0:
        return True, "errors=0"
    elif errors > 0:
        return False, f"errors={errors}"
    else:
        # 没有 errors 字段，检查 files 中的 error
        err_count = sum(1 for f in meta.get("files", []) if f.get("error"))
        if err_count == 0:
            return True, "No error fields set"
        return False, f"{err_count} files have errors"


def check_a7_expected_keys(meta: dict) -> tuple[bool, str]:
    """A7: meta.json 中能找到预期 key 名"""
    expected = {"CellResp", "CellXYZ", "periods"}
    meta_str = json.dumps(meta)
    found = {k for k in expected if k in meta_str}
    missing = expected - found
    if not missing:
        return True, f"All expected keys found: {found}"
    return False, f"Missing keys: {missing}, found: {found}"


ASSERTIONS = [
    ("A1", "Valid JSON", check_a1_valid_json),
    ("A2", "All 8 files listed", None),  # 需要 meta dict
    ("A3", "HDF5 shape/dtype recorded", None),
    ("A4", "v7.3 MAT detected", None),
    ("A5", "Wildcard merge exists", None),
    ("A6", "No unhandled errors", None),
    ("A7", "Expected keys present", None),
]


def grade_meta(meta_path: str) -> dict:
    """对一个 meta.json 运行全部 7 项断言"""
    results = {}

    # A1: 先检查 JSON 合法性
    passed, msg = check_a1_valid_json(meta_path)
    results["A1"] = {"pass": passed, "msg": msg}

    if not passed:
        # JSON 不合法，后续断言全部失败
        for aid in ["A2", "A3", "A4", "A5", "A6", "A7"]:
            results[aid] = {"pass": False, "msg": "Skipped (invalid JSON)"}
        return results

    with open(meta_path) as f:
        meta = json.load(f)

    for aid, check_fn in [
        ("A2", check_a2_all_files),
        ("A3", check_a3_shape_dtype),
        ("A4", check_a4_v73_detected),
        ("A5", check_a5_wildcard_merge),
        ("A6", check_a6_no_errors),
        ("A7", check_a7_expected_keys),
    ]:
        passed, msg = check_fn(meta)
        results[aid] = {"pass": passed, "msg": msg}

    return results


def grade_all(results_dir: str) -> dict:
    """扫描 results_dir 下所有 meta_*.json 文件并评分"""
    all_grades = {}
    results_path = Path(results_dir)

    for meta_file in sorted(results_path.rglob("meta*.json")):
        name = str(meta_file.relative_to(results_path))
        grades = grade_meta(str(meta_file))
        all_grades[name] = grades

    return all_grades


def print_report(all_grades: dict):
    """打印评分报告"""
    print("=" * 80)
    print("GRADING REPORT")
    print("=" * 80)

    for name, grades in all_grades.items():
        passed = sum(1 for g in grades.values() if g["pass"])
        total = len(grades)
        print(f"\n--- {name} [{passed}/{total}] ---")
        for aid in sorted(grades):
            g = grades[aid]
            status = "PASS" if g["pass"] else "FAIL"
            print(f"  {aid}: [{status}] {g['msg']}")

    # 汇总表
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("-" * 80)
    print(f"{'File':<50} {'Pass':>4} {'Total':>5} {'Rate':>6}")
    print("-" * 80)
    for name, grades in all_grades.items():
        passed = sum(1 for g in grades.values() if g["pass"])
        total = len(grades)
        rate = passed / total * 100 if total > 0 else 0
        print(f"{name:<50} {passed:>4} {total:>5} {rate:>5.0f}%")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: grade_results.py <meta.json> [meta2.json ...]")
        print("   or: grade_results.py --dir <results_directory>")
        sys.exit(1)

    if sys.argv[1] == "--dir":
        all_grades = grade_all(sys.argv[2])
    else:
        all_grades = {}
        for path in sys.argv[1:]:
            # 使用相对路径中的 system/eval 部分作为 key
            parts = Path(path).parts
            # 尝试提取 system_X/eY 部分
            name = "/".join(parts[-3:-1]) if len(parts) >= 3 else path
            all_grades[name] = grade_meta(path)

    print_report(all_grades)

    # 输出 JSON 格式
    output_json = {name: {k: v for k, v in grades.items()} for name, grades in all_grades.items()}
    json_path = "grading_results.json"
    with open(json_path, "w") as f:
        json.dump(output_json, f, indent=2)
    print(f"\nJSON results saved to {json_path}")
