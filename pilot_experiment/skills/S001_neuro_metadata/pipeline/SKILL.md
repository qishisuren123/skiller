# Neuroscience Data File Metadata Extraction

## Overview
This skill helps create a robust Python CLI script that scans directories for neuroscience data files (HDF5 and MATLAB formats) and extracts metadata while handling various edge cases, file corruption, and data type complexities.

## Workflow
1. **Input Validation**: Verify the target directory exists and is actually a directory
2. **File Discovery**: Recursively scan for .h5 and .mat files
3. **Progress Tracking**: Pre-scan files to provide accurate progress feedback
4. **Safe File Processing**: Use try-catch blocks around all file operations
5. **Format-Specific Handling**: 
   - HDF5: Use h5py visitor pattern to traverse datasets
   - MATLAB: Try scipy.io.loadmat first, fall back to h5py for v7.3 files
6. **Data Type Conversion**: Convert NumPy types to JSON-serializable Python types
7. **Path Management**: Store relative paths for portability
8. **Output Generation**: Write structured JSON metadata

## Common Pitfalls
- **NumPy Serialization**: NumPy integers/floats aren't JSON serializable - use conversion helper
- **MATLAB v7.3 Internal References**: Filter out variables starting with '#' (internal MATLAB references)
- **Cell Arrays**: Don't assume all MATLAB variables have simple shapes - use safe extraction
- **Absolute Paths**: Always convert to relative paths for portability
- **File Corruption**: Wrap all file operations in try-catch to continue processing
- **Complex Data Types**: Handle object arrays, cell arrays, and structured data gracefully

## Error Handling
- Log errors for corrupted files but continue processing
- Validate input directory existence and type
- Return None from processing functions on failure
- Use safe shape/dtype extraction for complex MATLAB types
- Graceful fallback from scipy.io to h5py for MATLAB v7.3

## Quick Reference
