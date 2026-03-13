# neuro-metadata-gen Pitfalls

Five common pitfalls encountered when scanning neuroscience data files, with root cause analysis and fixes.

---

## Pitfall 1: MATLAB v7.3 Files Raise OSError with scipy

**Error:**

```
OSError: Can't read data (no appropriate function for conversion path)
```

or

```
NotImplementedError: Please use HDF reader for matlab v7.3 files
```

**Root Cause:**

MATLAB v7.3 (introduced in MATLAB R2006b) stores `.mat` files in HDF5 format internally. `scipy.io.loadmat` only supports the older v5/v7 binary format. When it encounters a v7.3 file, it either raises `NotImplementedError` (common case) or `OSError` (edge case with partially readable headers).

**Fix:**

Implement a try-fallback pattern: attempt `scipy.io.loadmat` first, catch both `NotImplementedError` and `OSError`, then re-read the file with `h5py.File` which natively understands HDF5.

**Code:**

```python
def scan_mat(filepath, max_depth=None):
    result = {"file": filepath, "datasets": [], "error": None}

    # Attempt 1: scipy (v5/v7)
    try:
        mat = sio.loadmat(filepath, squeeze_me=False)
        # ... process mat dict ...
        return result
    except (NotImplementedError, OSError) as exc:
        logger.info("MATLAB v7.3 detected for %s, falling back to h5py.", filepath)

    # Attempt 2: h5py (v7.3 / HDF5)
    try:
        h5_result = scan_h5(filepath, max_depth=max_depth)
        result["format"] = "mat-v7.3 (hdf5)"
        result["datasets"] = h5_result["datasets"]
    except Exception as exc:
        result["error"] = str(exc)

    return result
```

---

## Pitfall 2: Nested HDF5 Groups Missed (Only Reading Top-Level Keys)

**Error:**

The output meta.json only lists top-level datasets (e.g., `"eeg"`, `"metadata"`) but misses deeply nested datasets like `"eeg/raw"`, `"eeg/filtered"`, `"metadata/events/triggers"`. The reported `total_datasets` count is suspiciously low.

**Root Cause:**

A naive implementation iterates over `f.keys()` at the root level and treats every key as a dataset. However, HDF5 files commonly use groups (analogous to directories) to organize data hierarchically. Groups contain other groups and datasets. Simply reading top-level keys misses everything below the first level.

```python
# WRONG: only reads root-level items
with h5py.File(filepath, "r") as f:
    for key in f.keys():
        datasets.append({"path": key, "shape": f[key].shape})
        # This crashes if f[key] is a Group (no .shape attribute)
```

**Fix:**

Implement a recursive traversal function that descends into every group. At each level, check whether an item is a `h5py.Dataset` or `h5py.Group`. Only record metadata for datasets; recurse into groups.

**Code:**

```python
def _recurse_h5_group(group, datasets, current_depth, max_depth):
    for key in group.keys():
        try:
            obj = group[key]
        except Exception:
            continue

        name = obj.name.lstrip("/")

        if isinstance(obj, h5py.Dataset):
            datasets.append({
                "path": name,
                "shape": tuple(obj.shape),
                "dtype": str(obj.dtype),
                "nbytes": int(obj.nbytes),
            })
        elif isinstance(obj, h5py.Group):
            if max_depth is None or (current_depth + 1) < max_depth:
                _recurse_h5_group(obj, datasets, current_depth + 1, max_depth)
```

---

## Pitfall 3: Path Prefix `./` in Relative Paths

**Error:**

The `file` field in meta.json contains paths like `"./sub-001_eeg.h5"` instead of `"sub-001_eeg.h5"`. Worse, when a file is at the root of the scan directory, `os.path.relpath` returns `"."` (just a dot), which is meaningless as a file path.

**Root Cause:**

`os.path.relpath(filepath, root)` produces platform-dependent results:

- If `filepath` equals `root`, it returns `"."`.
- On some systems, files in the immediate root directory get a `"./"` prefix.
- This breaks downstream tools that expect clean relative paths.

```python
>>> os.path.relpath("/data/study/sub-001.h5", "/data/study")
'sub-001.h5'       # OK on most systems

>>> os.path.relpath("/data/study/", "/data/study")
'.'                 # Problematic
```

**Fix:**

After computing the relative path, explicitly strip the leading `"./"` or replace a bare `"."` with the filename.

**Code:**

```python
rel_path = os.path.relpath(filepath_str, str(root))

# Fix bare '.' (file is the root directory itself -- unlikely but defensive)
if rel_path == ".":
    rel_path = fpath.name

# Strip leading './' or '.\\' on Windows
elif rel_path.startswith("." + os.sep):
    rel_path = rel_path[2:]
```

---

## Pitfall 4: Large File Hangs During Deep Inspection

**Error:**

The scanner appears to hang indefinitely (or consumes excessive memory and eventually gets OOM-killed) when processing a large HDF5 file (e.g., a 50 GB whole-brain fMRI dataset or a raw MEG recording).

**Root Cause:**

Large neuroscience HDF5 files can contain:

- Deeply nested group hierarchies (10+ levels for some BIDS-derivative formats).
- Thousands of small datasets per group (e.g., per-channel, per-trial storage).
- Compressed chunks that h5py must partially decompress to read metadata.

Recursing through the entire structure without any depth limit causes the scanner to spend minutes or hours on a single file, defeating the purpose of a quick metadata overview.

**Fix:**

Implement a configurable depth limit. Before opening a file, check its size on disk. If it exceeds the threshold (default 2 GB), set `max_depth = 2` to only inspect the top two levels. Record deeper groups as placeholder entries with `dtype = "group (depth-limited)"`.

**Code:**

```python
file_size = os.path.getsize(filepath_str)
max_depth = None

if file_size > large_threshold:
    max_depth = 2
    logger.info("Large file (%s). Limiting depth to %d.", format_size(file_size), max_depth)

# In the recursive traversal:
if isinstance(obj, h5py.Group):
    if max_depth is not None and current_depth >= max_depth:
        datasets.append({
            "path": name + "/",
            "shape": None,
            "dtype": "group (depth-limited)",
            "nbytes": 0,
        })
    else:
        _recurse_h5_group(obj, datasets, current_depth + 1, max_depth)
```

---

## Pitfall 5: Shape Comparison Too Strict for Subject Merging

**Error:**

Wildcard pattern merging is enabled, and the scanner correctly groups `sub-001_eeg.h5` through `sub-050_eeg.h5` by their generalized path `sub-*_eeg.h5`. However, it refuses to merge them -- each file appears individually in meta.json with `"merged": false`. The log says "structure differs; not merging."

**Root Cause:**

The default shape comparison uses exact matching. In a typical EEG or fMRI study, the first dimension (dim-0) represents the number of time points, trials, or epochs, which varies per subject. For example:

| Subject | Dataset `eeg/raw` shape | Dataset `eeg/events` shape |
|---------|------------------------|---------------------------|
| sub-001 | (15360, 64) | (48, 3) |
| sub-002 | (16128, 64) | (51, 3) |
| sub-003 | (14592, 64) | (45, 3) |

With exact comparison, `(15360, 64) != (16128, 64)`, so the signatures differ and merging fails.

**Fix:**

Implement a `--shape-mode` flag with three options:

- `exact`: Full shape comparison (for datasets where shapes must truly match).
- `flexible` (default): Replace dim-0 with a sentinel value (`-1`) before comparing. This way, `(-1, 64)` == `(-1, 64)` regardless of the actual first dimension.
- `ndim_only`: Only compare the number of dimensions (most lenient).

Additionally, collect dim-0 ranges across the merged group so users still know the actual range of variation.

**Code:**

```python
def compute_structure_signature(file_info, shape_mode="flexible"):
    items = []
    for ds in file_info.get("datasets", []):
        shape = ds.get("shape")
        if shape is None:
            shape_key = None
        elif shape_mode == "exact":
            shape_key = tuple(shape)
        elif shape_mode == "flexible":
            shape_key = (-1, *shape[1:]) if len(shape) > 0 else ()
        elif shape_mode == "ndim_only":
            shape_key = len(shape)
        items.append((ds["path"], ds["dtype"], shape_key))
    items.sort()
    return tuple(items)
```
