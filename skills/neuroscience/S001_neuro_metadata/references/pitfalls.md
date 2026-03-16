## MATLAB v7.3 File Format Error

**Error**: `Mat 4 and 5 mat-file header missing` when processing MATLAB files
**Root Cause**: MATLAB v7.3 files use HDF5 format internally, which scipy.io cannot read
**Fix**: Implement fallback to h5py when scipy.io fails, as v7.3 files are HDF5-compatible

## JSON Serialization Error

**Error**: `TypeError: Object of type int64 is not JSON serializable`
**Root Cause**: NumPy data types (int64, float64) are not JSON serializable
**Fix**: Create make_json_serializable() function to convert NumPy types to Python native types

## Memory Overflow with Large Files

**Error**: Process killed due to memory usage when processing large files
**Root Cause**: Using scipy.io.loadmat() loads entire file into memory
**Fix**: Use scipy.io.whosmat() to extract metadata without loading data, and ensure h5py only accesses metadata properties

## NaN/Infinity JSON Error

**Error**: `OverflowError: cannot convert float infinity to integer`
**Root Cause**: NaN and infinity values in dataset shapes/sizes cannot be converted to JSON
**Fix**: Check for NaN/infinity values and convert them to null in JSON output

## Recursion Depth Error

**Error**: `RecursionError: maximum recursion depth exceeded` with deeply nested HDF5 files
**Root Cause**: h5py.visititems() uses recursion which hits Python's recursion limit
**Fix**: Implement iterative traversal using deque with configurable maximum depth limit

## Inconsistent Output Format

**Error**: Different field names ("datasets" vs "variables") for HDF5 and MATLAB files
**Root Cause**: Original implementation used different naming conventions
**Fix**: Standardize to use "datasets" for both file types and "name" instead of "path" for consistency
