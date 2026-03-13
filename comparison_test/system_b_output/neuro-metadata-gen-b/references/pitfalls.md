# Common Pitfalls

## Pitfall 1: MATLAB v7.3 Files Cause scipy Failure

**Error**:
```
ValueError: Unknown mat file type, version 0, 0
```
or:
```
NotImplementedError: Please use HDF reader for matlab v7.3 files.
```

**Root Cause**: MATLAB's `-v7.3` save option writes HDF5-formatted files. The
file header contains HDF5 magic bytes instead of MATLAB magic bytes, so scipy's
format detection fails.

**Fix**: Wrap `scipy.io.loadmat()` in try/except, catch `ValueError`,
`NotImplementedError`, and `OSError`, then re-open with `h5py.File()`.

```python
try:
    mat = sio.loadmat(filepath)
except (NotImplementedError, ValueError, OSError):
    # v7.3 detected — fallback to h5py
    with h5py.File(filepath, "r") as f:
        ...
```

## Pitfall 2: scipy Injects Metadata Keys

**Error**: Output includes unexpected keys like `__header__`, `__version__`.

**Root Cause**: `scipy.io.loadmat()` adds three metadata keys to every loaded
dict: `__header__`, `__version__`, `__globals__`.

**Fix**: Filter keys that start with double underscore:
```python
for key, val in mat.items():
    if key.startswith("__"):
        continue
```

## Pitfall 3: Nested HDF5 Groups Missed

**Error**: Only top-level keys reported; nested datasets like
`/recording/eeg/data` are missing.

**Root Cause**: Using `f.keys()` only returns top-level items. HDF5 files can
have deeply nested group hierarchies.

**Fix**: Recursively walk groups:
```python
def walk_h5(group, prefix, datasets, depth, max_depth):
    for key in group:
        obj = group[key]
        if isinstance(obj, h5py.Dataset):
            datasets.append(...)
        elif isinstance(obj, h5py.Group):
            walk_h5(obj, f"{prefix}/{key}", datasets, depth+1, max_depth)
```

## Pitfall 4: Shape Mismatch Prevents Merging

**Error**: Files that should merge have different structure signatures.

**Root Cause**: The first dimension (usually number of neurons) varies across
subjects. With `exact` shape comparison, `(100, 500)` != `(120, 500)`.

**Fix**: Use `--shape-compare flex` (default) to replace dim-0 with -1 before
comparison. This way `(100, 500)` and `(120, 500)` both become `(-1, 500)`.

## Pitfall 5: Large Files Cause Hangs or OOM

**Error**: Script appears to hang when processing multi-GB HDF5 files.

**Root Cause**: Files with thousands of datasets at deep nesting levels take
very long to fully traverse.

**Fix**: Apply a depth limit for files exceeding a size threshold (default 2 GB).
Only top-level and second-level items are reported; deeper groups are marked as
`depth-limited`.
