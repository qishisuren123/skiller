# JSON Serialization Error

**Error**: TypeError: Object of type int64 is not JSON serializable

**Root Cause**: NumPy data types (int64, float64) are not directly JSON serializable, causing the json.dump() function to fail when trying to serialize results containing NumPy arrays or scalar values.

**Fix**: Convert all NumPy data types to native Python types using explicit float() and int() conversions before JSON serialization. Ensure all dictionary keys and values are native Python types.

# Scipy Dependency Issue  

**Error**: ModuleNotFoundError: No module not found: scipy

**Root Cause**: Script imported scipy.interpolate for linear interpolation, but scipy was not available in the environment and added unnecessary dependency complexity.

**Fix**: Implement manual linear interpolation using basic mathematical formula: y = y1 + (x - x1) * (y2 - y1) / (x2 - x1). Create helper function for interpolation without external dependencies.

# Data Parsing Whitespace Error

**Error**: ValueError: could not convert string to float: '12.5\n'

**Root Cause**: Input data contained newline characters and whitespace that weren't handled during parsing, causing float conversion to fail on strings with trailing characters.

**Fix**: Implement robust parsing with strip() to remove whitespace/newlines, try-except blocks for conversion errors, and treat malformed values as missing data (NaN).

# Incorrect Threshold Logic

**Error**: 0 extreme events found despite high precipitation values exceeding calculated threshold

**Root Cause**: Threshold calculation logic was backwards - treated higher return periods as corresponding to lower precipitation values, and used minimum precipitation for extrapolation instead of maximum.

**Fix**: Correct the relationship understanding - higher return periods correspond to higher (more extreme) precipitation values. Use extrapolation beyond maximum return period to estimate higher thresholds.
