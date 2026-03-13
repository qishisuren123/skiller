# Neuroscience Data Structure Scanner

## Overview
This skill helps create a CLI tool that recursively scans directories containing HDF5 and MATLAB files from neuroscience experiments, extracting metadata about internal data structures and generating a comprehensive JSON manifest.

## Workflow
1. **Setup argument parsing** with positional directory argument and optional output path
2. **Implement recursive file discovery** to find all .h5 and .mat files in directory tree
3. **Create HDF5 metadata extractor** that traverses groups and catalogs datasets with paths, shapes, and dtypes
4. **Build MATLAB file handler** that attempts scipy.io.loadmat first, then falls back to h5py for v7.3 files
5. **Implement error handling wrapper** that logs corrupted files but continues processing
6. **Structure metadata collection** into standardized format with file paths and dataset information
7. **Generate JSON output** with proper formatting and write to specified output file

## Common Pitfalls
- **MATLAB v7.3 detection**: scipy.io.loadmat fails silently on v7.3 files - catch the exception and retry with h5py
- **HDF5 group traversal**: Use h5py.visititems() rather than manual recursion to avoid infinite loops with circular references
- **Dtype serialization**: NumPy dtypes aren't JSON serializable - convert to string representation using str(dtype)
- **Memory issues with large files**: Don't load actual data arrays, only extract metadata using dataset.shape and dataset.dtype
- **Path handling**: Use os.path.relpath() to store relative paths in JSON for portability across systems

## Error Handling
- Wrap file operations in try-except blocks to catch corrupted files, permission errors, and format issues
- Log specific error messages with file paths for debugging while continuing the scan
- Handle both OSError (file system issues) and library-specific exceptions (h5py.File errors, scipy.io errors)
- Validate that directories exist before scanning and create output directory if needed

## Quick Reference
