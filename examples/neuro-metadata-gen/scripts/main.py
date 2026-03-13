#!/usr/bin/env python3
"""
neuro-metadata-gen: Scan neuroscience data directories and generate structured
metadata (meta.json) for .h5, .hdf5, and .mat files.

Features:
  - Recursive directory scanning with pathlib.rglob
  - HDF5 inspection with recursive group/dataset traversal
  - MATLAB .mat reading via scipy with auto-fallback to h5py for v7.3 format
  - Configurable large-file depth limiting (default threshold: 2 GB)
  - Wildcard pattern merging: group files by generalized path, compare
    structure signatures, collect dim0 ranges across merged files
  - Three shape comparison modes: exact, flexible (ignore dim0), ndim_only
  - JSON output with summary, scan_config, and files sections
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
    print("ERROR: numpy is required. Install with: pip install numpy>=1.24.0")
    sys.exit(1)

try:
    import h5py
except ImportError:
    print("ERROR: h5py is required. Install with: pip install h5py>=3.9.0")
    sys.exit(1)

try:
    import scipy.io as sio
except ImportError:
    print("ERROR: scipy is required. Install with: pip install scipy>=1.11.0")
    sys.exit(1)

try:
    from tqdm import tqdm
except ImportError:
    # Fallback: a no-op wrapper that just iterates
    def tqdm(iterable, **kwargs):
        return iterable


logger = logging.getLogger("neuro-metadata-gen")


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def format_size(nbytes: int) -> str:
    """Return a human-readable file-size string (e.g. '1.23 GB')."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(nbytes) < 1024.0:
            return f"{nbytes:.2f} {unit}"
        nbytes /= 1024.0
    return f"{nbytes:.2f} PB"


# ---------------------------------------------------------------------------
# HDF5 inspection
# ---------------------------------------------------------------------------

def inspect_h5_item(name: str, obj, datasets: list, current_depth: int,
                    max_depth: int | None) -> None:
    """Visitor callback for h5py items (groups and datasets).

    Appends a dict with path, shape, dtype, and nbytes for every dataset
    encountered.  Respects *max_depth* — if set, groups deeper than this
    level are silently skipped.

    Parameters
    ----------
    name : str
        HDF5 internal path of the item (e.g. ``"group1/dataset_a"``).
    obj : h5py.Dataset | h5py.Group
        The HDF5 object.
    datasets : list
        Accumulator list; dataset info dicts are appended here.
    current_depth : int
        Depth of *obj* relative to the file root (root children = 1).
    max_depth : int | None
        Maximum depth to recurse into.  ``None`` means unlimited.
    """
    if isinstance(obj, h5py.Dataset):
        try:
            shape = tuple(obj.shape)
            dtype = str(obj.dtype)
            nbytes = int(obj.nbytes) if hasattr(obj, "nbytes") else 0
        except Exception:
            shape = ()
            dtype = "unknown"
            nbytes = 0
        datasets.append({
            "path": name,
            "shape": shape,
            "dtype": dtype,
            "nbytes": nbytes,
        })
    elif isinstance(obj, h5py.Group):
        # If depth limiting is active, do not recurse further
        if max_depth is not None and current_depth >= max_depth:
            datasets.append({
                "path": name + "/",
                "shape": None,
                "dtype": "group (depth-limited)",
                "nbytes": 0,
            })


def scan_h5(filepath: str, max_depth: int | None = None) -> dict:
    """Open an HDF5 file and return a metadata dict with all datasets.

    Parameters
    ----------
    filepath : str
        Path to the .h5 / .hdf5 file.
    max_depth : int | None
        Maximum group recursion depth.  ``None`` = unlimited.

    Returns
    -------
    dict
        Keys: ``file``, ``size_bytes``, ``format``, ``datasets``, ``error``.
    """
    result = {
        "file": filepath,
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
            datasets: list[dict] = []
            _recurse_h5_group(f, datasets, current_depth=0,
                              max_depth=max_depth)
            result["datasets"] = datasets
    except Exception as exc:
        logger.warning("Failed to read HDF5 file %s: %s", filepath, exc)
        result["error"] = str(exc)

    return result


def _recurse_h5_group(group, datasets: list, current_depth: int,
                       max_depth: int | None) -> None:
    """Recursively walk an h5py.Group, collecting dataset metadata."""
    for key in group.keys():
        try:
            obj = group[key]
        except Exception:
            continue
        name = obj.name  # absolute HDF5 path, e.g. "/group1/data"
        # Strip leading '/' so paths look like "group1/data"
        name = name.lstrip("/")
        inspect_h5_item(name, obj, datasets, current_depth + 1, max_depth)

        # Recurse into sub-groups (unless depth-limited)
        if isinstance(obj, h5py.Group):
            if max_depth is None or (current_depth + 1) < max_depth:
                _recurse_h5_group(obj, datasets, current_depth + 1, max_depth)


# ---------------------------------------------------------------------------
# MATLAB .mat inspection
# ---------------------------------------------------------------------------

def scan_mat(filepath: str, max_depth: int | None = None) -> dict:
    """Read a MATLAB .mat file and return a metadata dict.

    Tries ``scipy.io.loadmat`` first.  If that raises an error (commonly for
    MATLAB v7.3 / HDF5-based .mat files), falls back to ``h5py``.

    Parameters
    ----------
    filepath : str
        Path to the .mat file.
    max_depth : int | None
        Passed through to :func:`scan_h5` when the v7.3 fallback is used.

    Returns
    -------
    dict
        Keys: ``file``, ``size_bytes``, ``format``, ``datasets``, ``error``.
    """
    result = {
        "file": filepath,
        "size_bytes": 0,
        "format": "mat",
        "datasets": [],
        "error": None,
    }
    try:
        result["size_bytes"] = os.path.getsize(filepath)
    except OSError:
        pass

    # --- Attempt 1: scipy.io.loadmat (works for v5 / v7) ---
    try:
        mat = sio.loadmat(filepath, squeeze_me=False)
        datasets = []
        for key, val in mat.items():
            if key.startswith("__"):
                # Skip scipy metadata keys (__header__, __version__, etc.)
                continue
            entry = {"path": key, "shape": None, "dtype": "unknown", "nbytes": 0}
            if isinstance(val, np.ndarray):
                entry["shape"] = tuple(val.shape)
                entry["dtype"] = str(val.dtype)
                entry["nbytes"] = int(val.nbytes)
            else:
                entry["dtype"] = type(val).__name__
            datasets.append(entry)
        result["datasets"] = datasets
        return result
    except NotImplementedError:
        # scipy raises NotImplementedError for v7.3 HDF5-based .mat files
        logger.info("MATLAB v7.3 detected for %s, falling back to h5py.",
                     filepath)
    except OSError as exc:
        # Some v7.3 files raise OSError instead
        logger.info("scipy OSError for %s (%s), falling back to h5py.",
                     filepath, exc)
    except Exception as exc:
        logger.warning("scipy.io.loadmat failed for %s: %s", filepath, exc)

    # --- Attempt 2: h5py fallback for MATLAB v7.3 ---
    try:
        h5_result = scan_h5(filepath, max_depth=max_depth)
        result["format"] = "mat-v7.3 (hdf5)"
        result["datasets"] = h5_result["datasets"]
        if h5_result["error"]:
            result["error"] = h5_result["error"]
    except Exception as exc:
        logger.warning("h5py fallback also failed for %s: %s", filepath, exc)
        result["error"] = str(exc)

    return result


# ---------------------------------------------------------------------------
# Structure signature & shape comparison
# ---------------------------------------------------------------------------

def compute_structure_signature(file_info: dict,
                                shape_mode: str = "flexible") -> tuple:
    """Compute a hashable signature that characterises the internal structure
    of a scanned file.

    Parameters
    ----------
    file_info : dict
        As returned by :func:`scan_h5` or :func:`scan_mat`.
    shape_mode : str
        One of ``"exact"``, ``"flexible"``, ``"ndim_only"``.

        - ``exact`` — full shape tuple is part of the signature.
        - ``flexible`` — first dimension is replaced with ``-1``.
        - ``ndim_only`` — only the number of dimensions is kept.

    Returns
    -------
    tuple
        A hashable signature.
    """
    items = []
    for ds in file_info.get("datasets", []):
        path = ds.get("path", "")
        dtype = ds.get("dtype", "")
        shape = ds.get("shape")

        if shape is None:
            shape_key: tuple | int | None = None
        elif shape_mode == "exact":
            shape_key = tuple(shape)
        elif shape_mode == "flexible":
            # Replace dim-0 with a wildcard sentinel
            shape_key = (-1, *shape[1:]) if len(shape) > 0 else ()
        elif shape_mode == "ndim_only":
            shape_key = len(shape)
        else:
            shape_key = tuple(shape)

        items.append((path, dtype, shape_key))

    # Sort for determinism
    items.sort()
    return tuple(items)


def collect_shape_ranges(file_infos: list[dict]) -> dict:
    """Given a list of file_info dicts that belong to the same merged group,
    collect the min/max of dim-0 for each dataset path.

    Returns
    -------
    dict
        Mapping from dataset path to ``{"min": int, "max": int}``.
    """
    dim0_map: dict[str, list[int]] = defaultdict(list)
    for fi in file_infos:
        for ds in fi.get("datasets", []):
            shape = ds.get("shape")
            if shape and len(shape) > 0 and isinstance(shape[0], (int, np.integer)):
                dim0_map[ds["path"]].append(int(shape[0]))

    ranges = {}
    for path, vals in dim0_map.items():
        ranges[path] = {"min": min(vals), "max": max(vals)}
    return ranges


# ---------------------------------------------------------------------------
# Wildcard pattern merging
# ---------------------------------------------------------------------------

def generalize_path(filepath: str, pattern: str) -> str:
    """Replace subject-specific tokens in *filepath* with a wildcard ``*``.

    Parameters
    ----------
    filepath : str
        The original relative file path.
    pattern : str
        A regex pattern whose first group (or the whole match) is replaced
        with ``*``.  Common example: ``subject_\\d+``  ->  ``subject_*``.

    Returns
    -------
    str
        The generalized path.
    """
    return re.sub(pattern, lambda m: re.sub(r"\d+", "*", m.group()), filepath)


def merge_by_pattern(file_results: list[dict], subject_pattern: str,
                     shape_mode: str) -> list[dict]:
    """Group scanned files by their generalized path, then merge groups that
    share the same structure signature.

    Parameters
    ----------
    file_results : list[dict]
        Each element is a file_info dict from scan_h5 / scan_mat.
    subject_pattern : str
        Regex passed to :func:`generalize_path`.
    shape_mode : str
        Passed through to :func:`compute_structure_signature`.

    Returns
    -------
    list[dict]
        A list of merged file entries.  Entries that could not be merged
        (unique files) are returned as-is with a ``"merged": False`` flag.
    """
    # Group by generalized path
    groups: dict[str, list[dict]] = defaultdict(list)
    for fi in file_results:
        gen_path = generalize_path(fi["file"], subject_pattern)
        groups[gen_path].append(fi)

    merged_entries = []
    for gen_path, members in groups.items():
        if len(members) == 1:
            # Single file — not merged
            entry = _file_info_to_entry(members[0])
            entry["merged"] = False
            entry["count"] = 1
            merged_entries.append(entry)
            continue

        # Check if all members share the same structure signature
        sigs = set()
        for m in members:
            sigs.add(compute_structure_signature(m, shape_mode))

        if len(sigs) == 1:
            # All share the same structure — merge them
            representative = members[0]
            dim0_ranges = collect_shape_ranges(members)
            total_bytes = sum(m.get("size_bytes", 0) for m in members)

            entry = _file_info_to_entry(representative)
            entry["file"] = gen_path
            entry["merged"] = True
            entry["count"] = len(members)
            entry["total_size_bytes"] = total_bytes
            entry["total_size_human"] = format_size(total_bytes)
            if dim0_ranges:
                entry["shape_dim0_ranges"] = dim0_ranges
            merged_entries.append(entry)
        else:
            # Structure mismatch — keep each file individually
            logger.info(
                "Pattern '%s' matched %d files but structure differs; "
                "not merging.", gen_path, len(members))
            for m in members:
                entry = _file_info_to_entry(m)
                entry["merged"] = False
                entry["count"] = 1
                merged_entries.append(entry)

    return merged_entries


def _file_info_to_entry(fi: dict) -> dict:
    """Convert an internal file_info dict to a JSON-friendly entry."""
    datasets_out = []
    for ds in fi.get("datasets", []):
        d = dict(ds)
        # Convert shape tuple to list for JSON serialization
        if d.get("shape") is not None:
            d["shape"] = list(d["shape"])
        datasets_out.append(d)

    return {
        "file": fi["file"],
        "size_bytes": fi.get("size_bytes", 0),
        "size_human": format_size(fi.get("size_bytes", 0)),
        "format": fi.get("format", "unknown"),
        "datasets": datasets_out,
        "error": fi.get("error"),
    }


# ---------------------------------------------------------------------------
# Summary builder
# ---------------------------------------------------------------------------

def build_summary(file_results: list[dict], elapsed: float) -> dict:
    """Compute aggregate statistics across all scanned files.

    Returns
    -------
    dict
        Summary statistics for the ``"summary"`` section of meta.json.
    """
    total_files = len(file_results)
    total_bytes = sum(f.get("size_bytes", 0) for f in file_results)
    total_datasets = sum(len(f.get("datasets", [])) for f in file_results)
    error_count = sum(1 for f in file_results if f.get("error"))

    format_counts: dict[str, int] = defaultdict(int)
    for f in file_results:
        fmt = f.get("format", "unknown")
        format_counts[fmt] += 1

    return {
        "total_files": total_files,
        "total_size_bytes": total_bytes,
        "total_size_human": format_size(total_bytes),
        "total_datasets": total_datasets,
        "errors": error_count,
        "format_breakdown": dict(format_counts),
        "scan_duration_seconds": round(elapsed, 2),
    }


# ---------------------------------------------------------------------------
# Main generation pipeline
# ---------------------------------------------------------------------------

def generate_meta(root_dir: str, output: str, merge: bool,
                  subject_pattern: str, shape_mode: str,
                  large_threshold: int, verbose: bool) -> None:
    """Top-level function: scan, inspect, (optionally) merge, write meta.json.

    Parameters
    ----------
    root_dir : str
        Root directory to scan.
    output : str
        Output path for meta.json.
    merge : bool
        Whether to apply wildcard pattern merging.
    subject_pattern : str
        Regex for subject-specific tokens (used by merge).
    shape_mode : str
        Shape comparison mode: exact | flexible | ndim_only.
    large_threshold : int
        Files larger than this (bytes) get depth-limited inspection.
    verbose : bool
        Enable DEBUG-level logging.
    """
    # Configure logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = Path(root_dir).resolve()
    if not root.is_dir():
        logger.error("Root directory does not exist: %s", root)
        sys.exit(1)

    logger.info("Scanning directory: %s", root)

    # Step 1: Discover files
    extensions = (".h5", ".hdf5", ".mat")
    discovered: list[Path] = []
    for ext in extensions:
        discovered.extend(root.rglob(f"*{ext}"))

    # Deduplicate and sort
    discovered = sorted(set(discovered))
    logger.info("Discovered %d files.", len(discovered))

    if not discovered:
        logger.warning("No .h5, .hdf5, or .mat files found under %s", root)

    # Step 2: Inspect each file
    start_time = time.time()
    file_results: list[dict] = []

    for fpath in tqdm(discovered, desc="Inspecting files", unit="file"):
        filepath_str = str(fpath)
        rel_path = os.path.relpath(filepath_str, str(root))
        # Avoid leading './' for files at the root level
        if rel_path == ".":
            rel_path = fpath.name
        elif rel_path.startswith("." + os.sep):
            rel_path = rel_path[2:]

        file_size = 0
        try:
            file_size = os.path.getsize(filepath_str)
        except OSError:
            pass

        # Determine depth limit for large files
        max_depth = None
        if file_size > large_threshold:
            max_depth = 2
            logger.info(
                "Large file detected (%s, %s). Limiting depth to %d.",
                rel_path, format_size(file_size), max_depth)

        suffix = fpath.suffix.lower()
        try:
            if suffix in (".h5", ".hdf5"):
                info = scan_h5(filepath_str, max_depth=max_depth)
            elif suffix == ".mat":
                info = scan_mat(filepath_str, max_depth=max_depth)
            else:
                continue
        except Exception as exc:
            logger.error("Unexpected error scanning %s: %s", rel_path, exc)
            info = {
                "file": filepath_str,
                "size_bytes": file_size,
                "format": suffix.lstrip("."),
                "datasets": [],
                "error": str(exc),
            }

        # Store the relative path for cleaner output
        info["file"] = rel_path
        file_results.append(info)

    elapsed = time.time() - start_time
    logger.info("Inspection complete in %.2f seconds.", elapsed)

    # Step 3: Optionally merge by wildcard pattern
    if merge and len(file_results) > 1:
        logger.info("Merging files by pattern: %s (shape_mode=%s)",
                     subject_pattern, shape_mode)
        files_section = merge_by_pattern(file_results, subject_pattern,
                                         shape_mode)
    else:
        files_section = []
        for fi in file_results:
            entry = _file_info_to_entry(fi)
            entry["merged"] = False
            entry["count"] = 1
            files_section.append(entry)

    # Step 4: Build summary
    summary = build_summary(file_results, elapsed)

    # Step 5: Assemble and write meta.json
    scan_config = {
        "root_dir": str(root),
        "merge_enabled": merge,
        "subject_pattern": subject_pattern if merge else None,
        "shape_mode": shape_mode,
        "large_file_threshold_bytes": large_threshold,
        "large_file_threshold_human": format_size(large_threshold),
    }

    meta = {
        "summary": summary,
        "scan_config": scan_config,
        "files": files_section,
    }

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False, default=str)

    logger.info("Metadata written to %s", output_path.resolve())
    logger.info("Summary: %d files, %s total, %d datasets, %d errors.",
                summary["total_files"],
                summary["total_size_human"],
                summary["total_datasets"],
                summary["errors"])


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="neuro-metadata-gen",
        description=(
            "Scan neuroscience data directories (.h5, .hdf5, .mat) and "
            "generate a structured meta.json with dataset shapes, dtypes, "
            "sizes, and optional wildcard-pattern merging."
        ),
    )

    parser.add_argument(
        "root_dir",
        help="Root directory to scan recursively for data files.",
    )
    parser.add_argument(
        "--output", "-o",
        default="meta.json",
        help="Output path for the generated metadata file (default: meta.json).",
    )
    parser.add_argument(
        "--merge",
        action=argparse.BooleanOptionalAction,
        default=True,
        help=(
            "Enable/disable wildcard pattern merging. When enabled, files "
            "matching the subject pattern with identical structure are grouped "
            "together. Use --no-merge to disable. (default: enabled)"
        ),
    )
    parser.add_argument(
        "--subject-pattern",
        default=r"(?:sub|subject|subj|sbj|SUB)[-_]?\d+",
        help=(
            "Regex pattern for subject-specific tokens to generalize during "
            "merging (default: '(?:sub|subject|subj|sbj|SUB)[-_]?\\d+')."
        ),
    )
    parser.add_argument(
        "--shape-mode",
        choices=["exact", "flexible", "ndim_only"],
        default="flexible",
        help=(
            "Shape comparison mode for merging. 'exact' requires identical "
            "shapes; 'flexible' ignores the first dimension (dim-0); "
            "'ndim_only' only checks the number of dimensions. "
            "(default: flexible)"
        ),
    )
    parser.add_argument(
        "--large-threshold",
        type=int,
        default=2 * 1024 * 1024 * 1024,  # 2 GB
        help=(
            "File size threshold in bytes above which depth-limited "
            "inspection is used. (default: 2147483648 = 2 GB)"
        ),
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG-level) logging.",
    )

    args = parser.parse_args()

    generate_meta(
        root_dir=args.root_dir,
        output=args.output,
        merge=args.merge,
        subject_pattern=args.subject_pattern,
        shape_mode=args.shape_mode,
        large_threshold=args.large_threshold,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
