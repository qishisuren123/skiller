## Polar Plot Array Dimension Error

**Error**: `ValueError: setting an array element with a sequence` when creating polar bar charts

**Root Cause**: Matplotlib polar projection `ax.bar()` function had issues with array indexing using `theta[:-1]` and improper `bottom` parameter handling

**Fix**: Use proper theta center calculations with `np.linspace(0, 2*np.pi, 16, endpoint=False)` and fix bottom array updates with explicit addition instead of in-place operations

## CSV Column Detection Failure

**Error**: `KeyError: 'wind_speed_ms'` when CSV files use different column naming conventions

**Root Cause**: Hard-coded default column names don't match actual CSV file column names, causing immediate failure without fallback

**Fix**: Implement auto-detection function that searches for common meteorological column name patterns and provides clear error messages listing available columns when detection fails

## Memory Error with Large Datasets

**Error**: `MemoryError` when processing large datasets (50,000+ records) during matplotlib figure creation

**Root Cause**: Passing raw data arrays to matplotlib plotting functions causes memory issues with large datasets, even though data is already binned

**Fix**: Pre-calculate frequency matrices during statistics calculation and pass only the 16x4 frequency matrix to plotting function instead of raw data arrays
