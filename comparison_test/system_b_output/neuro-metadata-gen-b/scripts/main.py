#!/usr/bin/env python3
"""
neuro-metadata-gen-b: 扫描神经科学数据目录，提取 HDF5/MATLAB 文件内部结构元数据，
生成 meta.json 目录。

由 requirement-to-skill 流程生成。
"""

import argparse
import json
import logging
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

try:
    import numpy as np
except ImportError:
    sys.exit("ERROR: numpy is required. Install with: pip install numpy>=1.24.0")

try:
    import h5py
except ImportError:
    sys.exit("ERROR: h5py is required. Install with: pip install h5py>=3.9.0")

try:
    import scipy.io as sio
except ImportError:
    sys.exit("ERROR: scipy is required. Install with: pip install scipy>=1.11.0")

logger = logging.getLogger("neuro-metadata-gen-b")

EXTENSIONS = (".h5", ".hdf5", ".mat")
# 大文件阈值，超过此值时限制 HDF5 递归深度
LARGE_FILE_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB


def human_size(nbytes: int) -> str:
    """将字节数转为人类可读格式"""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(nbytes) < 1024.0:
            return f"{nbytes:.2f} {unit}"
        nbytes /= 1024.0
    return f"{nbytes:.2f} PB"


# ---------------------------------------------------------------------------
# HDF5 检查
# ---------------------------------------------------------------------------

def walk_h5(group, prefix: str, datasets: list, depth: int, max_depth: int | None):
    """递归遍历 HDF5 group，收集 dataset 元数据"""
    if max_depth is not None and depth >= max_depth:
        return
    for key in group:
        try:
            obj = group[key]
        except Exception:
            continue
        full_path = f"{prefix}/{key}" if prefix else key
        if isinstance(obj, h5py.Dataset):
            try:
                shape = list(obj.shape)
                dtype = str(obj.dtype)
                nbytes = int(obj.nbytes) if hasattr(obj, "nbytes") else 0
            except Exception:
                shape, dtype, nbytes = [], "unknown", 0
            datasets.append({
                "key": full_path,
                "shape": shape,
                "dtype": dtype,
                "nbytes": nbytes,
            })
        elif isinstance(obj, h5py.Group):
            walk_h5(obj, full_path, datasets, depth + 1, max_depth)


def inspect_h5(filepath: str, max_depth: int | None = None) -> dict:
    """打开 HDF5 文件，返回元数据字典"""
    result = {
        "path": filepath,
        "size_bytes": 0,
        "format": "hdf5",
        "datasets": [],
        "error": None,
    }
    try:
        result["size_bytes"] = os.path.getsize(filepath)
    except OSError:
        pass
    try:
        with h5py.File(filepath, "r") as f:
            datasets = []
            walk_h5(f, "", datasets, 0, max_depth)
            result["datasets"] = datasets
    except Exception as e:
        logger.warning("Failed to read HDF5 %s: %s", filepath, e)
        result["error"] = str(e)
    return result


# ---------------------------------------------------------------------------
# MATLAB .mat 检查
# ---------------------------------------------------------------------------

def inspect_mat(filepath: str, max_depth: int | None = None) -> dict:
    """读取 .mat 文件，自动检测 v7.3 并 fallback 到 h5py"""
    result = {
        "path": filepath,
        "size_bytes": 0,
        "format": "mat",
        "datasets": [],
        "error": None,
    }
    try:
        result["size_bytes"] = os.path.getsize(filepath)
    except OSError:
        pass

    # 尝试 1: scipy.io.loadmat（v5/v7 格式）
    try:
        mat = sio.loadmat(filepath, squeeze_me=False)
        datasets = []
        for key, val in mat.items():
            if key.startswith("__"):
                continue  # 跳过 scipy 元数据 (__header__ 等)
            entry = {"key": key, "shape": [], "dtype": "unknown", "nbytes": 0}
            if isinstance(val, np.ndarray):
                entry["shape"] = list(val.shape)
                entry["dtype"] = str(val.dtype)
                entry["nbytes"] = int(val.nbytes)
            else:
                entry["dtype"] = type(val).__name__
            datasets.append(entry)
        result["datasets"] = datasets
        return result
    except NotImplementedError:
        logger.info("v7.3 detected (NotImplementedError) for %s, fallback to h5py", filepath)
    except (ValueError, OSError) as e:
        logger.info("scipy failed for %s (%s), fallback to h5py", filepath, e)
    except Exception as e:
        logger.warning("scipy.io.loadmat unexpected error for %s: %s", filepath, e)

    # 尝试 2: h5py fallback（v7.3 = HDF5）
    try:
        h5_result = inspect_h5(filepath, max_depth=max_depth)
        result["format"] = "mat-v7.3-hdf5"
        result["datasets"] = h5_result["datasets"]
        if h5_result["error"]:
            result["error"] = h5_result["error"]
    except Exception as e:
        logger.warning("h5py fallback also failed for %s: %s", filepath, e)
        result["error"] = str(e)

    return result


# ---------------------------------------------------------------------------
# 结构签名与通配符合并
# ---------------------------------------------------------------------------

def structure_signature(file_info: dict, mode: str = "flex") -> tuple:
    """计算文件结构签名，用于合并时比较"""
    items = []
    for ds in file_info.get("datasets", []):
        key = ds.get("key", "")
        dtype = ds.get("dtype", "")
        shape = ds.get("shape", [])
        if mode == "exact":
            shape_key = tuple(shape)
        elif mode == "flex":
            shape_key = (-1,) + tuple(shape[1:]) if shape else ()
        elif mode == "ndim":
            shape_key = len(shape)
        else:
            shape_key = tuple(shape)
        items.append((key, dtype, shape_key))
    items.sort()
    return tuple(items)


def generalize_path(path: str, pattern: str) -> str:
    """将路径中的 subject 标识替换为通配符 *"""
    return re.sub(pattern, lambda m: re.sub(r"\d+", "*", m.group()), path)


def dim0_ranges(file_infos: list[dict]) -> dict:
    """收集合并组中各 dataset 的 dim-0 范围"""
    ranges = defaultdict(list)
    for fi in file_infos:
        for ds in fi.get("datasets", []):
            shape = ds.get("shape", [])
            if shape and isinstance(shape[0], (int, float)):
                ranges[ds["key"]].append(int(shape[0]))
    return {k: {"min": min(v), "max": max(v)} for k, v in ranges.items()}


def merge_files(file_results: list[dict], subject_regex: str,
                shape_mode: str) -> list[dict]:
    """按通配符路径分组，合并结构一致的文件"""
    groups = defaultdict(list)
    for fi in file_results:
        gen = generalize_path(fi["path"], subject_regex)
        groups[gen].append(fi)

    merged = []
    for gen_path, members in groups.items():
        if len(members) == 1:
            entry = dict(members[0])
            entry["merged"] = False
            entry["count"] = 1
            entry["size_human"] = human_size(entry.get("size_bytes", 0))
            merged.append(entry)
            continue

        sigs = {structure_signature(m, shape_mode) for m in members}
        if len(sigs) == 1:
            # 结构一致，合并
            rep = dict(members[0])
            total_bytes = sum(m.get("size_bytes", 0) for m in members)
            rep["path"] = gen_path
            rep["merged"] = True
            rep["count"] = len(members)
            rep["total_size_bytes"] = total_bytes
            rep["total_size_human"] = human_size(total_bytes)
            rep["size_human"] = human_size(rep.get("size_bytes", 0))
            rep["dim0_ranges"] = dim0_ranges(members)
            # 将 shape 中的 dim-0 替换为 -1 表示通配
            for ds in rep.get("datasets", []):
                if ds.get("shape") and len(ds["shape"]) > 0:
                    ds["shape"][0] = -1
            merged.append(rep)
        else:
            logger.info("Pattern '%s': %d files but structure differs, not merging",
                        gen_path, len(members))
            for m in members:
                entry = dict(m)
                entry["merged"] = False
                entry["count"] = 1
                entry["size_human"] = human_size(entry.get("size_bytes", 0))
                merged.append(entry)
    return merged


# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

def scan_directory(data_dir: str, output: str, merge: bool,
                   subject_regex: str, shape_compare: str, verbose: bool):
    """扫描目录 → 检查文件 → 合并 → 输出 meta.json"""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    root = Path(data_dir).resolve()
    if not root.is_dir():
        logger.error("Directory not found: %s", root)
        sys.exit(1)

    logger.info("Scanning: %s", root)

    # 发现文件
    files = sorted({p for ext in EXTENSIONS for p in root.rglob(f"*{ext}")})
    logger.info("Found %d files", len(files))

    if not files:
        logger.warning("No HDF5/MAT files found under %s", root)

    # 逐个检查
    start = time.time()
    results = []
    for fpath in files:
        rel = os.path.relpath(str(fpath), str(root))
        fsize = os.path.getsize(str(fpath)) if fpath.exists() else 0
        max_depth = 2 if fsize > LARGE_FILE_BYTES else None

        ext = fpath.suffix.lower()
        try:
            if ext in (".h5", ".hdf5"):
                info = inspect_h5(str(fpath), max_depth)
            elif ext == ".mat":
                info = inspect_mat(str(fpath), max_depth)
            else:
                continue
        except Exception as e:
            logger.error("Unexpected error on %s: %s", rel, e)
            info = {"path": rel, "size_bytes": fsize, "format": ext.lstrip("."),
                    "datasets": [], "error": str(e)}

        info["path"] = rel
        results.append(info)

    elapsed = time.time() - start
    logger.info("Inspection done in %.2fs", elapsed)

    # 合并
    if merge and len(results) > 1:
        files_section = merge_files(results, subject_regex, shape_compare)
    else:
        files_section = []
        for r in results:
            entry = dict(r)
            entry["merged"] = False
            entry["count"] = 1
            entry["size_human"] = human_size(entry.get("size_bytes", 0))
            files_section.append(entry)

    # 汇总
    total_files = len(results)
    total_bytes = sum(r.get("size_bytes", 0) for r in results)
    total_datasets = sum(len(r.get("datasets", [])) for r in results)
    error_count = sum(1 for r in results if r.get("error"))
    fmt_counts = defaultdict(int)
    for r in results:
        fmt_counts[r.get("format", "unknown")] += 1

    summary = {
        "total_files": total_files,
        "total_size_bytes": total_bytes,
        "total_size_human": human_size(total_bytes),
        "total_datasets": total_datasets,
        "errors": error_count,
        "format_counts": dict(fmt_counts),
        "scan_seconds": round(elapsed, 2),
    }

    meta = {
        "summary": summary,
        "scan_config": {
            "root": str(root),
            "merge": merge,
            "subject_regex": subject_regex if merge else None,
            "shape_compare": shape_compare,
        },
        "files": files_section,
    }

    out_path = Path(output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Written to %s", out_path.resolve())
    logger.info("Summary: %d files, %s, %d datasets, %d errors",
                total_files, human_size(total_bytes), total_datasets, error_count)


def main():
    parser = argparse.ArgumentParser(
        prog="neuro-metadata-gen-b",
        description="Scan neuroscience data directories and generate meta.json",
    )
    parser.add_argument("data_dir", help="Root data directory to scan")
    parser.add_argument("-o", "--output", default="meta.json",
                        help="Output JSON path (default: meta.json)")
    parser.add_argument("--merge", action=argparse.BooleanOptionalAction, default=True,
                        help="Enable/disable wildcard merging (default: enabled)")
    parser.add_argument("--subject-regex",
                        default=r"(?:sub|subject|subj|sbj|SUB)[-_]?\d+",
                        help="Regex for subject directory tokens")
    parser.add_argument("--shape-compare", choices=["exact", "flex", "ndim"],
                        default="flex", help="Shape comparison mode (default: flex)")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug logging")
    args = parser.parse_args()

    scan_directory(
        data_dir=args.data_dir,
        output=args.output,
        merge=args.merge,
        subject_regex=args.subject_regex,
        shape_compare=args.shape_compare,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
