# Data Loading Errors

## Error: ValueError when loading CSV files with headers
**Root Cause**: Using np.loadtxt() on CSV files with headers and text-based NaN values
**Fix**: Replace with pandas.read_csv() with comprehensive na_values parameter to handle various NaN representations

## Error: Boolean array truth value ambiguity in spike detection
**Root Cause**: Direct boolean operations on arrays containing NaN values causing ambiguous truth evaluation
**Fix**: Implement explicit NaN masking before boolean operations and use proper array indexing for comparisons

## Error: JSON serialization of NaN values
**Root Cause**: NumPy NaN values are not valid JSON and serialize as strings instead of null
**Fix**: Add safe_json_convert() function to convert NaN/inf values to JSON null and ensure statistics are computed on QC'd data rather than original arrays
