# SKILL: Neuroscience Data Structure Scanner

## Overview
A Python CLI tool that recursively scans directories for HDF5 (.h5) and MATLAB (.mat) files from neuroscience experiments, extracts metadata about internal data structures (dataset paths, shapes, dtypes), and outputs a comprehensive JSON summary. Handles both standard MATLAB files and v7.3 format gracefully.

## Workflow

1. **Parse Arguments**: Use argparse to get root directory and optional output path
2. **Discover Files**: Recursively walk directory tree to find all .h5 and .mat files
3. **Process HDF5 Files**: Use h5py to traverse groups and extract dataset metadata
4. **Process MATLAB Files**: Try scipy.io.loadmat first, fallback to h5py for v7.3 format
5. **Extract Metadata**: For each file, collect dataset/variable names, shapes, and dtypes
6. **Handle Errors**: Log corrupted files but continue processing remaining files
7. **Output JSON**: Write structured metadata to specified output file

## Common Pitfalls & Solutions

1. **MATLAB v7.3 Format Issues**
   - *Problem*: scipy.io.loadmat fails on v7.3 files
   - *Solution*: Catch exception and fallback to h5py (v7.3 uses HDF5 format)

2. **Corrupted File Handling**
   - *Problem*: Single corrupted file crashes entire scan
   - *Solution*: Wrap file processing in try-except, log error, continue with next file

3. **Memory Issues with Large Files**
   - *Problem*: Loading entire datasets into memory
   - *Solution*: Only read metadata (shapes, dtypes) without loading actual data arrays

4. **Nested HDF5 Group Traversal**
   - *Problem*: Missing datasets in deeply nested groups
   - *Solution*: Use recursive visititems() or manual stack-based traversal

5. **JSON Serialization of NumPy Types**
   - *Problem*: NumPy dtypes not JSON serializable
   - *Solution*: Convert dtypes to strings using str() or custom JSON encoder

## Error Handling Tips

- Use `logging` module to track processing progress and errors
- Implement file-level try-except blocks to isolate failures
- Check file permissions before attempting to read
- Validate JSON output before writing to ensure proper formatting
- Use context managers (`with` statements) for file operations

## Reference Code Snippet

```python
import h5py
import scipy.io
import json
import logging
from pathlib import Path

def extract_hdf5_metadata(filepath):
    """Extract metadata from HDF5 file."""
    datasets = []
    try:
        with h5py.File(filepath, 'r') as f:
            def visitor(name, obj):
                if isinstance(obj, h5py.Dataset):
                    datasets.append({
                        'path': name,
                        'shape': list(obj.shape),
                        'dtype': str(obj.dtype)
                    })
            f.visititems(visitor)
    except Exception as e:
        logging.error(f"Failed to read HDF5 {filepath}: {e}")
    return datasets

def extract_mat_metadata(filepath):
    """Extract metadata from MATLAB file with v7.3 fallback."""
    variables = []
    try:
        # Try standard MATLAB format first
        data = scipy.io.loadmat(filepath, struct_as_record=False)
        for name, var in data.items():
            if not name.startswith('__'):
                variables.append({
                    'name': name,
                    'shape': list(var.shape) if hasattr(var, 'shape') else [],
                    'dtype': str(var.dtype) if hasattr(var, 'dtype') else 'unknown'
                })
    except NotImplementedError:
        # Fallback to h5py for v7.3 format
        variables = extract_hdf5_metadata(filepath)
    except Exception as e:
        logging.error(f"Failed to read MAT {filepath}: {e}")
    return variables
```