#!/usr/bin/env python3
"""
neuro-metadata-gen-c: 扫描神经科学数据目录，提取文件内部结构元数据。
由 skill-creator 流程生成。
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
    sys.exit("numpy required: pip install numpy")

try:
    import h5py
except ImportError:
    sys.exit("h5py required: pip install h5py")

try:
    import scipy.io as sio
except ImportError:
    sys.exit("scipy required: pip install scipy")

log = logging.getLogger("neuro-meta")


def fmt_size(n: int) -> str:
    for u in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"


def scan_hdf5(path: str, max_depth: int | None = None) -> dict:
    """扫描 HDF5 文件，返回元数据字典"""
    info = {"path": path, "size": 0, "format": "hdf5", "datasets": [], "error": None}
    try:
        info["size"] = os.path.getsize(path)
    except OSError:
        pass

    def _walk(grp, prefix, depth):
        if max_depth and depth >= max_depth:
            return
        for k in grp:
            try:
                obj = grp[k]
            except Exception:
                continue
            p = f"{prefix}/{k}" if prefix else k
            if isinstance(obj, h5py.Dataset):
                try:
                    info["datasets"].append({
                        "key": p, "shape": list(obj.shape),
                        "dtype": str(obj.dtype),
                        "bytes": int(obj.nbytes) if hasattr(obj, "nbytes") else 0
                    })
                except Exception:
                    info["datasets"].append({"key": p, "shape": [], "dtype": "?", "bytes": 0})
            elif isinstance(obj, h5py.Group):
                _walk(obj, p, depth + 1)

    try:
        with h5py.File(path, "r") as f:
            _walk(f, "", 0)
    except Exception as e:
        log.warning("HDF5 read failed %s: %s", path, e)
        info["error"] = str(e)
    return info


def scan_matlab(path: str, max_depth: int | None = None) -> dict:
    """扫描 MATLAB .mat 文件，自动检测 v7.3"""
    info = {"path": path, "size": 0, "format": "mat", "datasets": [], "error": None}
    try:
        info["size"] = os.path.getsize(path)
    except OSError:
        pass

    # 先尝试 scipy
    try:
        mat = sio.loadmat(path, squeeze_me=False)
        for k, v in mat.items():
            if k.startswith("__"):
                continue
            ds = {"key": k, "shape": [], "dtype": "unknown", "bytes": 0}
            if isinstance(v, np.ndarray):
                ds["shape"] = list(v.shape)
                ds["dtype"] = str(v.dtype)
                ds["bytes"] = int(v.nbytes)
            else:
                ds["dtype"] = type(v).__name__
            info["datasets"].append(ds)
        return info
    except (NotImplementedError, ValueError, OSError) as e:
        log.info("v7.3 detected for %s (%s), using h5py", path, type(e).__name__)
    except Exception as e:
        log.warning("scipy error on %s: %s", path, e)

    # h5py fallback
    try:
        h5 = scan_hdf5(path, max_depth)
        info["format"] = "mat-v7.3-hdf5"
        info["datasets"] = h5["datasets"]
        if h5["error"]:
            info["error"] = h5["error"]
    except Exception as e:
        info["error"] = str(e)
    return info


def compute_sig(entry: dict, mode: str) -> tuple:
    """计算文件结构签名"""
    items = []
    for d in entry.get("datasets", []):
        s = d.get("shape", [])
        if mode == "exact":
            sk = tuple(s)
        elif mode == "flexible":
            sk = (-1,) + tuple(s[1:]) if s else ()
        else:  # ndim_only
            sk = len(s)
        items.append((d.get("key", ""), d.get("dtype", ""), sk))
    return tuple(sorted(items))


def merge_subjects(results: list[dict], pattern: str, mode: str) -> list[dict]:
    """通配符合并"""
    groups = defaultdict(list)
    for r in results:
        gen = re.sub(pattern, lambda m: re.sub(r"\d+", "*", m.group()), r["path"])
        groups[gen].append(r)

    out = []
    for gen, members in groups.items():
        if len(members) == 1:
            e = dict(members[0])
            e["merged"] = False
            e["count"] = 1
            e["size_human"] = fmt_size(e.get("size", 0))
            out.append(e)
            continue

        sigs = {compute_sig(m, mode) for m in members}
        if len(sigs) == 1:
            rep = dict(members[0])
            total = sum(m.get("size", 0) for m in members)
            rep["path"] = gen
            rep["merged"] = True
            rep["count"] = len(members)
            rep["total_size"] = total
            rep["total_size_human"] = fmt_size(total)
            rep["size_human"] = fmt_size(rep.get("size", 0))
            # dim-0 范围统计
            ranges = defaultdict(list)
            for m in members:
                for d in m.get("datasets", []):
                    if d.get("shape") and len(d["shape"]) > 0:
                        ranges[d["key"]].append(d["shape"][0])
            rep["dim0_ranges"] = {k: {"min": min(v), "max": max(v)} for k, v in ranges.items()}
            for d in rep.get("datasets", []):
                if d.get("shape") and len(d["shape"]) > 0:
                    d["shape"][0] = -1
            out.append(rep)
        else:
            log.info("'%s' (%d files) structure differs, not merging", gen, len(members))
            for m in members:
                e = dict(m)
                e["merged"] = False
                e["count"] = 1
                e["size_human"] = fmt_size(e.get("size", 0))
                out.append(e)
    return out


def run(args):
    """主执行流程"""
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"
    )

    root = Path(args.data_dir).resolve()
    if not root.is_dir():
        log.error("Not a directory: %s", root)
        sys.exit(1)

    log.info("Scanning %s", root)

    # 发现文件
    exts = (".h5", ".hdf5", ".mat")
    files = sorted({p for e in exts for p in root.rglob(f"*{e}")})
    log.info("Found %d files", len(files))

    # 检查每个文件
    t0 = time.time()
    results = []
    for fp in files:
        rel = os.path.relpath(str(fp), str(root))
        sz = fp.stat().st_size if fp.exists() else 0
        depth_lim = 2 if sz > 2 * 1024**3 else None

        if fp.suffix.lower() in (".h5", ".hdf5"):
            r = scan_hdf5(str(fp), depth_lim)
        elif fp.suffix.lower() == ".mat":
            r = scan_matlab(str(fp), depth_lim)
        else:
            continue
        r["path"] = rel
        results.append(r)

    elapsed = time.time() - t0
    log.info("Done in %.2fs", elapsed)

    # 合并
    if args.merge and len(results) > 1:
        file_entries = merge_subjects(results, args.subject_pattern, args.shape_mode)
    else:
        file_entries = []
        for r in results:
            e = dict(r)
            e["merged"] = False
            e["count"] = 1
            e["size_human"] = fmt_size(e.get("size", 0))
            file_entries.append(e)

    # 汇总
    n_files = len(results)
    total_bytes = sum(r.get("size", 0) for r in results)
    n_datasets = sum(len(r.get("datasets", [])) for r in results)
    n_errors = sum(1 for r in results if r.get("error"))
    fmt_map = defaultdict(int)
    for r in results:
        fmt_map[r.get("format", "?")] += 1

    meta = {
        "summary": {
            "total_files": n_files,
            "total_size_bytes": total_bytes,
            "total_size_human": fmt_size(total_bytes),
            "total_datasets": n_datasets,
            "errors": n_errors,
            "format_counts": dict(fmt_map),
            "scan_duration_seconds": round(elapsed, 2),
        },
        "scan_config": {
            "root_dir": str(root),
            "merge_enabled": args.merge,
            "subject_pattern": args.subject_pattern if args.merge else None,
            "shape_mode": args.shape_mode,
        },
        "files": file_entries,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)

    log.info("Output: %s (%d files, %s, %d datasets, %d errors)",
             out.resolve(), n_files, fmt_size(total_bytes), n_datasets, n_errors)


def main():
    p = argparse.ArgumentParser(
        prog="neuro-metadata-gen-c",
        description="Scan neuroscience data directories and generate meta.json"
    )
    p.add_argument("data_dir", help="Root data directory")
    p.add_argument("-o", "--output", default="meta.json", help="Output path")
    p.add_argument("--merge", action=argparse.BooleanOptionalAction, default=True,
                   help="Enable wildcard merging")
    p.add_argument("--subject-pattern", default=r"(?:sub|subject|subj|sbj|SUB)[-_]?\d+",
                   help="Subject directory regex")
    p.add_argument("--shape-mode", choices=["exact", "flexible", "ndim_only"],
                   default="flexible", help="Shape comparison mode")
    p.add_argument("-v", "--verbose", action="store_true", help="Debug logging")
    args = p.parse_args()
    run(args)


if __name__ == "__main__":
    main()
