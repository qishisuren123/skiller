---
name: neuro-metadata-gen-c
description: "Generate fine-grained metadata catalogs (meta.json) for neuroscience data folders containing HDF5 and MATLAB files. Scans directories recursively, inspects internal file structure (keys, shapes, dtypes, sizes), handles MATLAB v7.3 format transparently, and optionally merges repeated subject structures into wildcard entries. Use this skill whenever the user needs to catalog, summarize, or inspect the structure of a scientific data directory — especially if it contains .h5, .hdf5, or .mat files, or mentions subjects/sessions/trials in a hierarchical folder layout."
---

# Neuroscience Data Metadata Generator

You are helping the user scan a neuroscience data directory and produce a structured `meta.json` that describes every HDF5 and MATLAB file's internal contents — without loading full data arrays into memory.

## Core workflow

1. **Discover files** — Recursively walk the root directory and collect all `.h5`, `.hdf5`, and `.mat` files. Print the count.

2. **Inspect each file** — For each file:
   - **HDF5** (`.h5`, `.hdf5`): Open with `h5py`, recursively walk groups and datasets. For each dataset, record its full path (e.g., `CellResp`), shape, dtype, and byte size.
   - **MATLAB** (`.mat`): Try `scipy.io.loadmat()` first. If it fails (MATLAB v7.3 files throw `ValueError` or `NotImplementedError`), fall back to `h5py`. Filter out scipy's internal keys (`__header__`, `__version__`, `__globals__`).

3. **Merge subjects** (optional) — If the data has repeated subject directories (e.g., `subject_01/`, `subject_02/`), check whether files at the same relative path share identical structure. If they do, collapse them into a single wildcard entry like `subject_*/TimeSeries.h5` with a count and dimension range summary.

4. **Write output** — Save `meta.json` with a summary section (total files, total size, format breakdown, error count) and a files section with per-file metadata.

## Key gotchas to watch for

**MATLAB v7.3 is secretly HDF5.** When MATLAB saves with `-v7.3`, the file is HDF5 internally. `scipy.io.loadmat()` will fail with `ValueError: Unknown mat file type` or `NotImplementedError`. You MUST catch this and re-open with `h5py`. Mark these files as `mat-v7.3-hdf5` format in the output.

**Don't forget nested HDF5 groups.** A naive approach reads only top-level keys, missing datasets nested inside groups. Always recurse into `h5py.Group` objects.

**Shape comparison needs flexibility.** When merging subjects, the first dimension (typically neuron count) varies per subject. Compare shapes by replacing dim-0 with a wildcard before checking structural consistency.

**Large files can hang.** For files > 2 GB, limit HDF5 traversal to 2 depth levels to avoid spending minutes crawling deeply nested structures.

## Expected neuroscience data keys

For reference, the typical HDF5 and MATLAB keys you'll encounter in zebrafish whole-brain datasets:

**TimeSeries.h5:**
- `CellResp` — neural activity (neurons × timepoints), float32
- `CellRespAvr` — trial-averaged activity
- `CellRespAvrZ` — z-scored trial-averaged activity
- `CellRespZ` — z-scored full activity
- `absIX` — absolute cell indices

**data_full.mat:**
- `periods`, `fpsec`, `numcell_full` — experiment parameters
- `CellXYZ`, `CellXYZ_norm` — cell spatial coordinates
- `anat_stack`, `anat_yx`, `anat_yz`, `anat_zx` — anatomical images
- `timelists`, `timelists_names` — stimulus timing
- `Behavior_raw`, `Behavior_full`, `BehaviorAvr` — behavioral data
- `Eye_full`, `Eye_avr` — eye tracking data

## Implementation

Use `scripts/main.py` for the complete CLI tool. It supports:
- `data_dir` — root directory to scan
- `--output` / `-o` — output path (default: `meta.json`)
- `--merge` / `--no-merge` — wildcard merging toggle
- `--subject-pattern` — regex for subject directories
- `--shape-mode` — `exact`, `flexible`, or `ndim_only`
- `--verbose` / `-v` — debug logging

See `references/data_formats.md` for detailed format documentation.

## Error handling

When something goes wrong:
1. **File read errors** — Catch and log, continue to next file. Don't halt the entire scan.
2. **v7.3 detection** — The error message will say "Unknown mat file type" or "Please use HDF reader". Fall back to h5py.
3. **Permission denied** — Log and skip. Common on network-mounted datasets.
4. **Malformed HDF5** — h5py may raise `OSError`. Log the error and record it in the file's `error` field.
