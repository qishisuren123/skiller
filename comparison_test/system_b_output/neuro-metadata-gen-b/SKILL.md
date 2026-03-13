---
name: neuro-metadata-gen-b
description: "Recursively scan neuroscience data directories containing HDF5 (.h5, .hdf5) and MATLAB (.mat) files, inspect their internal structure (dataset keys, shapes, dtypes, byte sizes), and produce a structured meta.json catalog. Automatically detects MATLAB v7.3 files and falls back to h5py when scipy.io.loadmat fails. Supports wildcard pattern merging to collapse repeated subject directory structures into single entries with dimension ranges. Use this skill when the user needs to generate a metadata summary of a hierarchical neuroscience dataset folder."
license: MIT
compatibility: "Python >=3.9; h5py >=3.9.0; scipy >=1.11.0; numpy >=1.24.0."
metadata:
  author: requirement-to-skill-generator
  version: "1.0"
---

# Neuroscience Data Metadata Generator

Scans directories of HDF5 and MATLAB files, reads their internal structure
without loading full arrays into memory, and outputs a structured `meta.json`
catalog. Handles MATLAB v7.3 format transparently and merges repeated subject
structures into wildcard entries.

## When to Use This Skill

- "Generate metadata for my neuroscience data folder"
- "What datasets and shapes are inside these HDF5 files?"
- "Catalog the internal structure of a multi-subject dataset"
- "I have .h5 and .mat files across many subjects, summarize them"
- "Detect which .mat files are v7.3 and read them with h5py"

## Inputs

- **data_dir** (required): Path to the root data directory
- **--output / -o**: Output JSON path (default: `meta.json`)
- **--merge / --no-merge**: Enable or disable wildcard pattern merging (default: enabled)
- **--subject-regex**: Regex pattern for subject directories (default: `subject_\d+`)
- **--shape-compare**: Shape comparison mode: `exact`, `flex`, `ndim` (default: `flex`)

## Workflow

1. **Discover**: Recursively find all `.h5`, `.hdf5`, `.mat` files
2. **Inspect HDF5**: Open with h5py, walk groups/datasets, record path/shape/dtype/bytes
3. **Inspect MAT**: Try scipy.io.loadmat; on failure, auto-fallback to h5py for v7.3
4. **Merge** (optional): Group files by generalized wildcard path, compare structure signatures, collapse consistent groups
5. **Output**: Write meta.json with summary and per-file metadata

Run `scripts/main.py --help` for all CLI options. See `references/workflow.md` for the detailed pipeline.

## Error Handling

Common errors and how to handle them:

1. **MATLAB v7.3 detection failure**: scipy.io.loadmat raises `ValueError` or `NotImplementedError` for v7.3 files. The tool catches these exceptions and falls back to h5py automatically. Troubleshoot by checking the `format` field in output — it should show `mat-v7.3-hdf5`.
2. **Deeply nested HDF5 groups**: Some HDF5 files have 10+ nesting levels. The tool walks recursively by default but applies a depth limit for files exceeding the size threshold.
3. **Permission or I/O errors**: Network-mounted data directories may have intermittent access issues. Each file is wrapped in try/except and errors are logged in the output rather than halting the scan.
4. **Structure mismatch during merge**: If subjects have inconsistent internal structure, the tool keeps them as individual entries and logs a warning.

## Common Pitfalls

1. **MATLAB v7.3 is actually HDF5**: Files saved with `-v7.3` flag have HDF5 headers, not MATLAB headers. Must detect scipy failure and re-open with h5py.
2. **scipy metadata keys**: `scipy.io.loadmat` injects `__header__`, `__version__`, `__globals__` keys that must be filtered out.
3. **Shape comparison across subjects**: The first dimension (neurons) varies per subject. Use `--shape-compare flex` to wildcard dim-0 during merge comparison.

See `references/pitfalls.md` for the full list with code examples.

## Output Format

```json
{
  "summary": {"total_files": 8, "total_size_human": "1.86 MB", "errors": 0},
  "files": [
    {"path": "Subjects/subject_*/TimeSeries.h5", "merged": true, "count": 3,
     "datasets": [{"key": "CellResp", "shape": [-1, 500], "dtype": "float32"}]}
  ]
}
```

See `assets/example_output.md` for a complete example.
