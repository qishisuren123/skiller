# B-Value Division by Zero Error

**Error**: ZeroDivisionError in b-value calculation when denominator becomes zero
**Root Cause**: Completeness magnitude equals mean magnitude, making (mean_mag - completeness_mag + bin_width/2) ≈ 0
**Fix**: Added check for near-zero denominator and adjust completeness magnitude by -0.1 if detected

# Non-Monotonic Histogram Bins Error

**Error**: ValueError: `bins` must increase monotonically when using np.histogram
**Root Cause**: Using np.arange with floating-point numbers creates precision errors in bin edges
**Fix**: Replaced np.arange with np.linspace and proper rounding of min/max magnitudes to ensure monotonic bins

# Performance Issues with Large Datasets

**Error**: Extremely slow processing (hours) for datasets with 50,000+ events due to nested loops
**Root Cause**: O(n²) complexity in aftershock identification with nested iteration over all events
**Fix**: Implemented vectorized operations using NumPy, time-based filtering first, and pandas vectorized calculations

# JSON Serialization Type Error

**Error**: TypeError: Object of type int64 is not JSON serializable
**Root Cause**: NumPy and pandas data types (int64, float64) are not natively JSON serializable
**Fix**: Created to_json_serializable() function to convert NumPy/pandas types to native Python types before JSON export
