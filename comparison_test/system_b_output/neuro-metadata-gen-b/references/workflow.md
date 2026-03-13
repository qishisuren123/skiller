# Workflow: Neuroscience Data Metadata Generation

## Step 1 — File Discovery

Recursively scan the root directory for files matching `.h5`, `.hdf5`, `.mat`
extensions using `pathlib.rglob`. Deduplicate and sort by path.

## Step 2 — HDF5 Inspection

For each `.h5` / `.hdf5` file:

1. Open with `h5py.File(path, "r")`
2. Recursively walk all groups and datasets
3. For each dataset, record: `key` (full HDF5 path), `shape`, `dtype`, `nbytes`
4. For large files (> 2 GB), limit recursion depth to 2 levels

Key datasets in neuroscience HDF5 files:
- `CellResp` — raw neural activity (neurons x timepoints)
- `CellRespAvr` — trial-averaged activity
- `CellRespAvrZ` — z-scored trial-averaged activity
- `absIX` — absolute cell indices

## Step 3 — MATLAB File Inspection

For each `.mat` file:

1. Try `scipy.io.loadmat(path, squeeze_me=False)`
2. Filter out scipy metadata keys (`__header__`, `__version__`, `__globals__`)
3. For each remaining variable, record key, shape, dtype, nbytes

Common MATLAB variables in neuroscience data:
- `periods`, `fpsec`, `numcell_full` — experiment parameters
- `CellXYZ`, `CellXYZ_norm` — cell spatial coordinates
- `anat_stack`, `anat_yx`, `anat_yz`, `anat_zx` — anatomical imaging
- `Behavior_raw`, `Behavior_full`, `BehaviorAvr` — behavioral time series

## Step 4 — MATLAB v7.3 Fallback

When `scipy.io.loadmat` raises `NotImplementedError`, `ValueError`, or `OSError`:

1. Log the detection: "v7.3 detected, falling back to h5py"
2. Re-open the `.mat` file with `h5py.File(path, "r")`
3. Walk HDF5 groups/datasets as in Step 2
4. Set format field to `mat-v7.3-hdf5`

Root cause: MATLAB's `-v7.3` save option produces HDF5-format files with a
MATLAB wrapper. scipy only handles v5/v7 format.

## Step 5 — Wildcard Pattern Merging

When `--merge` is enabled:

1. For each file, compute a generalized path by replacing subject tokens
   (matched by `--subject-regex`) with `*`
2. Group files by generalized path
3. For groups with 2+ members, compute structure signatures
4. If all signatures match, merge into a single entry with:
   - `merged: true`, `count: N`
   - `dim0_ranges` showing min/max of first dimension across subjects
5. If signatures differ, keep as individual entries

Shape comparison modes:
- `exact` — full shape must match
- `flex` — replace dim-0 with -1 before comparing (default)
- `ndim` — only compare number of dimensions

## Step 6 — JSON Output

Write `meta.json` with three sections:
- `summary` — aggregate statistics
- `scan_config` — parameters used for this run
- `files` — per-file metadata entries
