# neuro-metadata-gen Workflow

This document describes the six-step workflow that `neuro-metadata-gen` follows when scanning a neuroscience data directory and generating `meta.json`.

---

## Step 1: Directory Scanning with `pathlib.rglob`

The pipeline begins by recursively discovering all relevant data files under the user-supplied root directory. We use `pathlib.Path.rglob` to match three file extensions:

- `.h5` and `.hdf5` (HDF5 format, commonly used for large array storage)
- `.mat` (MATLAB format, both classic v5/v7 and modern v7.3/HDF5-based)

The discovery phase works as follows:

1. Resolve the root directory to an absolute path.
2. For each extension, call `root.rglob(f"*{ext}")` to collect matching paths.
3. Deduplicate (in case of symlink overlaps) and sort the results for deterministic ordering.
4. Convert each absolute path to a relative path from the root using `os.path.relpath`, taking care to strip leading `./` artifacts.

**Design rationale:** `pathlib.rglob` is preferred over `os.walk` + manual extension filtering because it handles symlinks, hidden directories, and permission errors more gracefully. The sorted output ensures that meta.json is reproducible across runs.

---

## Step 2: HDF5 Inspection with Recursive Group Traversal

For each `.h5` or `.hdf5` file, we open it with `h5py.File` in read-only mode and recursively traverse its internal hierarchy of groups and datasets.

The traversal algorithm:

1. Start at the root group (`/`).
2. Iterate over all keys in the current group.
3. For each key, check whether the item is a **Dataset** or a **Group**:
   - **Dataset:** Record its internal HDF5 path (e.g., `"eeg/raw"`), shape, dtype, and nbytes.
   - **Group:** Recurse into the group, incrementing the current depth counter.
4. The visitor function `inspect_h5_item` handles each item, appending dataset metadata to an accumulator list.

**Depth tracking:** Every recursive call increments a `current_depth` counter. This counter is compared against `max_depth` (see Step 4) to decide whether to descend into sub-groups.

**Error isolation:** Each individual key access is wrapped in `try/except` so that a corrupt dataset does not abort the entire file scan.

---

## Step 3: MATLAB File Reading with v7.3 Fallback

MATLAB `.mat` files come in two fundamentally different formats:

| Format | MATLAB Version | Internal Structure | Reader |
|--------|---------------|-------------------|--------|
| v5 / v7 | MATLAB 5.x--7.2 | Proprietary binary | `scipy.io.loadmat` |
| v7.3 | MATLAB 7.3+ | HDF5-based | `h5py` |

The reading strategy implements a **try-fallback** pattern:

1. **Primary attempt:** Call `scipy.io.loadmat(filepath, squeeze_me=False)`.
   - On success, iterate over the returned dict. Skip scipy metadata keys (those starting with `__`). For each remaining key, record shape, dtype, and nbytes if the value is an `np.ndarray`, otherwise record the Python type name.
2. **Fallback trigger:** `scipy.io.loadmat` raises `NotImplementedError` or `OSError` when it encounters a v7.3 file. When either exception is caught:
   - Log an informational message noting the v7.3 detection.
   - Delegate to `scan_h5()` which handles the file as a standard HDF5 container.
   - Tag the format as `"mat-v7.3 (hdf5)"` in the output.
3. **Total failure:** If both scipy and h5py fail, record the error string and return a partial result.

---

## Step 4: Large File Depth Limiting Strategy

Neuroscience datasets routinely contain files exceeding tens of gigabytes (e.g., raw fMRI time series, high-density EEG recordings). Fully traversing deeply nested HDF5 structures in such files can cause the scanner to hang for minutes or exhaust memory.

The depth limiting strategy:

1. Before inspecting any file, check its size on disk via `os.path.getsize`.
2. Compare against the configurable `--large-threshold` (default: 2 GB).
3. If the file exceeds the threshold, set `max_depth = 2` for the inspection call.
4. During recursive HDF5 traversal, when `current_depth >= max_depth`:
   - Do **not** recurse into the sub-group.
   - Instead, record a placeholder entry with `dtype = "group (depth-limited)"` and `shape = null`.
5. The placeholder signals to downstream consumers that the metadata is incomplete and the file should be re-inspected with a higher depth limit or a specialized tool.

**Threshold selection:** The 2 GB default was chosen based on empirical testing with common neuroimaging formats (NIfTI-in-HDF5, BrainVision exports). Users can adjust it with `--large-threshold` for their specific workload.

---

## Step 5: Wildcard Pattern Merging Algorithm

Neuroimaging studies typically produce one file per subject with an identical internal structure (e.g., `sub-001_eeg.h5`, `sub-002_eeg.h5`, ..., `sub-200_eeg.h5`). Listing all 200 files individually in meta.json is redundant. The merging algorithm groups them under a single wildcard entry.

### 5.1 Path Generalization

Each file's relative path is passed through `generalize_path(filepath, pattern)`:

1. Apply `re.sub(pattern, ...)` where the pattern is the user-configurable `--subject-pattern` (default: `(?:sub|subject|subj|sbj|SUB)[-_]?\d+`).
2. Within each match, replace all digit sequences with `*`.
3. Example: `raw/sub-042_task-rest.h5` becomes `raw/sub-*_task-rest.h5`.

### 5.2 Grouping

Files are grouped into a `dict[str, list[dict]]` keyed by their generalized path.

### 5.3 Structure Signature Comparison

For each group with more than one member, compute a **structure signature** for every file:

1. Extract the list of `(path, dtype, shape_key)` tuples from the file's datasets.
2. The `shape_key` depends on the `--shape-mode`:
   - `exact`: full shape tuple, e.g. `(200, 64, 512)`.
   - `flexible`: replace dim-0 with `-1`, e.g. `(-1, 64, 512)`. This accounts for varying numbers of trials/samples per subject.
   - `ndim_only`: just the number of dimensions, e.g. `3`.
3. Sort the tuples and convert to a hashable `tuple`.

If all members of a group share the same signature, they are merged.

### 5.4 dim-0 Range Collection

For merged groups, `collect_shape_ranges` iterates over all member files and, for each dataset path, collects the dim-0 values into a list. The output records `min` and `max`, e.g.:

```json
"shape_dim0_ranges": {
  "eeg/raw": {"min": 180, "max": 220},
  "eeg/events": {"min": 45, "max": 63}
}
```

### 5.5 Non-Mergeable Files

If the signatures within a generalized-path group differ (e.g., one subject has an extra dataset), all members are emitted individually with `"merged": false`.

---

## Step 6: JSON Output Generation with Summary Statistics

The final step assembles the three top-level sections of `meta.json` and writes them to disk.

### 6.1 `summary` Section

Computed by `build_summary()`, this section provides aggregate statistics:

- `total_files`: Number of files scanned.
- `total_size_bytes` / `total_size_human`: Aggregate size.
- `total_datasets`: Sum of all datasets found across all files.
- `errors`: Count of files that produced errors during scanning.
- `format_breakdown`: A dict mapping format strings (e.g., `"hdf5"`, `"mat"`, `"mat-v7.3 (hdf5)"`) to file counts.
- `scan_duration_seconds`: Wall-clock time for the inspection phase.

### 6.2 `scan_config` Section

Records the configuration used for this scan so that results are reproducible:

- `root_dir`: Absolute path that was scanned.
- `merge_enabled`: Whether merging was active.
- `subject_pattern`: The regex used for path generalization (or `null` if merging was off).
- `shape_mode`: The shape comparison mode.
- `large_file_threshold_bytes` / `large_file_threshold_human`: The depth-limiting threshold.

### 6.3 `files` Section

A list of file entries. Each entry contains:

- `file`: Relative path (or wildcard pattern if merged).
- `size_bytes` / `size_human`: File size (or representative file size for merged entries).
- `format`: Detected format string.
- `datasets`: List of dataset descriptors with `path`, `shape`, `dtype`, `nbytes`.
- `error`: Error string or `null`.
- `merged`: Boolean indicating whether this is a merged group.
- `count`: Number of files represented (1 for non-merged).
- `total_size_bytes` / `total_size_human`: (merged only) Aggregate size across all member files.
- `shape_dim0_ranges`: (merged only) Per-dataset dim-0 range dict.

### 6.4 Writing

The assembled dict is serialized with `json.dump(meta, f, indent=2, ensure_ascii=False, default=str)`. The `default=str` fallback ensures that any non-serializable types (e.g., `numpy.int64`) are gracefully converted. Parent directories for the output path are created with `mkdir(parents=True, exist_ok=True)`.
