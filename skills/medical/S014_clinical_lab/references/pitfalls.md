# JSON Serialization Error

**Error**: TypeError: Object of type int64 is not JSON serializable

**Root Cause**: Pandas int64 and numpy data types cannot be directly serialized to JSON format.

**Fix**: Convert pandas/numpy types to native Python types using int() and str(), and add default=str parameter to json.dump().

# Missing Value Crashes

**Error**: TypeError: '<' not supported between instances of 'float' and 'NoneType'

**Root Cause**: Attempting to compare NaN values or missing reference ranges without proper null checking.

**Fix**: Use pd.isna() to check for missing values before any mathematical operations, and return appropriate default values ('unknown' flags, False for critical).

# Inflexible String Matching

**Error**: Unit conversions not applied to test names with different cases or formats.

**Root Cause**: Using exact string equality (==) instead of flexible matching for test names like "Glucose" vs "GLUCOSE" vs "Blood Glucose".

**Fix**: Use case-insensitive substring matching with str.contains('glucose', case=False, na=False) instead of exact equality.

# Performance Issues with Large Datasets

**Error**: Script hangs or becomes extremely slow with datasets over 10,000 records.

**Root Cause**: Using pandas apply() functions with lambda expressions creates row-by-row processing bottlenecks.

**Fix**: Replace apply() with vectorized operations using boolean masks and .loc[] indexing for bulk operations.

# Unit Conversion Logic Bug

**Error**: Critical value detection fails because normalized test values are compared against non-normalized reference ranges.

**Root Cause**: Normalizing test values to SI units but leaving reference ranges in original units, causing unit mismatch in comparisons.

**Fix**: Normalize both test values AND reference ranges (reference_low, reference_high) using the same conversion factors to maintain consistent units.
