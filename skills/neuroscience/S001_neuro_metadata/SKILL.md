---
name: neuro_metadata
description: "Write a standalone Python CLI script that recursively scans a directory containing HDF5 (.h5) and MATLAB (.mat) files from a neuroscience experiment, extracts internal structure metadata (dataset paths, shapes, dtypes), and outputs to JSON format with proper error handling for large files, corrupted data, and deep nested structures."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: neuroscience
---

# Neuro Metadata

## Overview
This skill creates a Python CLI tool for extracting metadata from neuroscience data files without loading actual data into memory. It handles both HDF5 (.h5, .hdf5) and MATLAB (.mat) files, including MATLAB v7.3 format, with robust error handling for corrupted files, memory constraints, and deeply nested structures.

## When to Use
- Cataloging large neuroscience datasets without memory overhead
- Auditing file structures across experiment directories
- Identifying corrupted or problematic data files
- Creating metadata inventories for data management
- Preprocessing step before data analysis pipelines

## Inputs
- `directory`: Root directory path containing HDF5/MATLAB files
- `--output` (optional): Output JSON filename (default: meta.json)

## Workflow
1. Execute `scripts/main.py` with target directory
2. Script recursively scans for .h5/.hdf5/.mat files
3. For each file, extracts metadata using appropriate method:
   - HDF5: Uses h5py with iterative traversal to avoid recursion limits
   - MATLAB: Uses scipy.io.whosmat() for memory efficiency, falls back to h5py for v7.3 files
4. Handles edge cases: NaN/infinity values, JSON serialization, memory constraints
5. Outputs standardized JSON with consistent "datasets" structure
6. Provides error summary for failed files
7. Reference workflow details in `references/workflow.md`

## Error Handling
The script implements comprehensive error handling strategies:
- Memory overflow protection using metadata-only extraction
- Recursion depth limits for deeply nested structures  
- JSON serialization error handling for NumPy types and NaN/infinity values
- Graceful fallback from scipy.io to h5py for MATLAB v7.3 files
- Global error tracking with detailed error reporting in output

## Common Pitfalls
- Using scipy.io.loadmat() loads entire files into memory - use whosmat() instead
- NumPy data types aren't JSON serializable - implement conversion functions
- MATLAB v7.3 files require h5py, not scipy.io
- Deep nested HDF5 structures can cause recursion errors - use iterative traversal
- NaN/infinity values break JSON serialization - convert to null values

## Output Format
