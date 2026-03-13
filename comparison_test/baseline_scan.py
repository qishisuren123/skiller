#!/usr/bin/env python3
"""
baseline_scan.py: 无技能 baseline —— 模拟 Claude 在没有 skill 指导时的"朴素"方法。
只做基本的文件发现和浅层检查，不处理 v7.3 fallback，不做通配符合并。
"""

import json
import os
import sys
from pathlib import Path

try:
    import h5py
except ImportError:
    h5py = None

try:
    import scipy.io as sio
except ImportError:
    sio = None

try:
    import numpy as np
except ImportError:
    np = None


def scan_dir(root_dir: str, output: str):
    root = Path(root_dir).resolve()
    files_meta = []
    errors = 0

    for fpath in sorted(root.rglob("*")):
        if fpath.suffix.lower() not in (".h5", ".hdf5", ".mat"):
            continue
        rel = os.path.relpath(str(fpath), str(root))
        entry = {"file": rel, "size": os.path.getsize(str(fpath))}

        if fpath.suffix.lower() in (".h5", ".hdf5") and h5py:
            try:
                with h5py.File(str(fpath), "r") as f:
                    entry["keys"] = list(f.keys())
                    entry["format"] = "hdf5"
            except Exception as e:
                entry["error"] = str(e)
                errors += 1
        elif fpath.suffix.lower() == ".mat" and sio:
            try:
                mat = sio.loadmat(str(fpath))
                entry["keys"] = [k for k in mat if not k.startswith("__")]
                entry["format"] = "mat"
            except Exception as e:
                # baseline 不做 v7.3 fallback
                entry["error"] = str(e)
                entry["format"] = "mat-error"
                errors += 1
        else:
            entry["keys"] = []
            entry["format"] = "unknown"

        files_meta.append(entry)

    meta = {
        "summary": {
            "total_files": len(files_meta),
            "errors": errors,
        },
        "files": files_meta,
    }

    with open(output, "w") as f:
        json.dump(meta, f, indent=2)

    print(f"Baseline scan: {len(files_meta)} files, {errors} errors -> {output}")


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    output = sys.argv[2] if len(sys.argv) > 2 else "meta.json"
    scan_dir(root, output)
