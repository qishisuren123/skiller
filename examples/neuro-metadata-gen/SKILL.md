---
name: neuro-metadata-gen
description: "Recursively scan neuroscience data directories containing HDF5 and MATLAB files, extract internal structure metadata (keys, shapes, dtypes), and generate a structured meta.json catalog. Supports MATLAB v7.3 auto-fallback via h5py, large file depth limiting, and wildcard pattern merging for consistent subject structures. Use this skill when the user needs to catalog the internal structure of a neuroscience dataset folder."
license: MIT
compatibility: "Python >=3.9; h5py >=3.9.0; scipy >=1.11.0; numpy >=1.24.0. Optional: tqdm for progress bars."
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Neuroscience Dataset Metadata Generator

Recursively scans directories of HDF5 (`.h5`, `.hdf5`) and MATLAB (`.mat`)
files, reads their internal structure without loading data into memory, and
produces a comprehensive `meta.json` describing keys, shapes, dtypes, and
file sizes. Wildcard merging collapses repeated subject structures into a
single entry.

## When to Use This Skill

- "Catalog the structure of my neuroscience data folder"
- "What keys and shapes are inside all these HDF5 files?"
- "Generate a metadata summary for a multi-subject dataset"
- "Check which subjects have inconsistent file structures"
- "I have hundreds of .h5 and .mat files, summarize them"

## Inputs

- **root_dir** (required): Path to the dataset root directory
- **--output** (optional): Output JSON path (default: `meta.json`)
- **--merge / --no-merge**: Enable/disable wildcard pattern merging
- **--subject-pattern**: Regex for subject directories (default: `subject_\d+`)
- **--shape-mode**: Shape comparison strategy (`exact`, `flexible`, `ndim_only`)
- **--large-threshold**: Large file depth-limit threshold in GB (default: 2.0)

## Workflow

1. **Scan**: Recursively find all `.h5`, `.hdf5`, `.mat` files under root directory
2. **Inspect HDF5**: Traverse nested groups/datasets, record shape, dtype, size
3. **Inspect MAT**: Try `scipy.io.loadmat` first; auto-fallback to `h5py` for v7.3
4. **Merge** (optional): Group by wildcard pattern, compare structure signatures
5. **Output**: Write `meta.json` with summary, scan config, and file metadata

Run `scripts/main.py --help` for full CLI options. See `references/workflow.md` for details.

## Error Handling

Common errors and how to handle them:

1. **`OSError: Unable to open file (file signature not found)`**: MATLAB v7.3 files fail with `scipy.io.loadmat`. The tool handles this automatically by catching `NotImplementedError` and falling back to `h5py`.
2. **Large file hangs**: Files over the threshold (default 2 GB) are depth-limited to 2 levels. Troubleshoot by adjusting `--large-threshold`.
3. **`KeyError` on MATLAB struct fields**: Some `.mat` files have internal `#refs#` groups. The tool handles this by filtering keys starting with `#`.
4. **Permission errors on network drives**: If scan fails on certain files, the error is caught and logged; processing continues for remaining files.

## Common Pitfalls

1. **MATLAB v7.3 format**: `.mat` files saved with `-v7.3` are actually HDF5 internally. `scipy.io.loadmat` raises `NotImplementedError`; must fallback to `h5py`.
2. **Nested HDF5 groups**: Only reading top-level keys misses nested datasets like `/recording/eeg/data`. Must recurse into groups.
3. **Shape comparison across subjects**: First dimension (time/samples) varies per subject. Use `--shape-mode flexible` to ignore it during merging.

See `references/pitfalls.md` for the full list with code examples.

## Output Format

```json
{
  "summary": {
    "total_files": 90,
    "total_size_human": "11.5 GB",
    "format_counts": {"hdf5": 30, "matlab_legacy": 45, "matlab_v73": 15}
  },
  "files": {
    "subject_*/eeg_raw.h5": {
      "pattern": "subject_*/eeg_raw.h5",
      "matched_count": 30,
      "structure_consistent": true,
      "contents": {"recording/eeg/data": {"shape": [12000, 64], "dtype": "float32"}}
    }
  }
}
```

See `assets/example_output.md` for a complete example.
