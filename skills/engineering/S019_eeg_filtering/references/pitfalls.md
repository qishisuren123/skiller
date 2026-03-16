## File I/O Operation Error

**Error**: ValueError: I/O operation on closed file during CSV writing
**Root Cause**: Concurrent file operations or premature file handle closure
**Fix**: Implement explicit file operations with proper error handling and sequential chunk writing

## NaN Values Causing Filter Instability

**Error**: RuntimeWarning: invalid value encountered in divide during filtering
**Root Cause**: NaN values in raw EEG data causing numerical instability in filter operations
**Fix**: Add signal cleaning function to interpolate NaN values and clip extreme outliers before filtering

## PSD Array Length Mismatch

**Error**: ValueError: arrays must all be the same length when creating PSD DataFrame
**Root Cause**: Welch's method returning different frequency arrays for different channels
**Fix**: Use consistent nperseg parameter and establish reference frequency array from first channel

## Memory Overflow with Large Datasets

**Error**: MemoryError when processing hours of EEG data
**Root Cause**: Loading entire dataset into memory simultaneously
**Fix**: Implement chunked processing with streaming output and downsampled PSD computation

## NumPy Data Type Conversion Error

**Error**: TypeError: result_type() got unexpected keyword argument during PSD computation
**Root Cause**: Mixed data types in accumulated arrays causing scipy.signal compatibility issues
**Fix**: Ensure explicit float64 dtype conversion and use .tolist() when accumulating data across chunks
