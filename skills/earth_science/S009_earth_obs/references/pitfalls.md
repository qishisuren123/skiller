# Common Pitfalls and Solutions

## Pandas fillna Method Deprecation

**Error**: `AttributeError: DataFrame.fillna() got an unexpected keyword argument 'method'`

**Root Cause**: The `method` parameter in `fillna()` was deprecated in pandas 2.0+ and removed in newer versions.

**Fix**: Replace `fillna(method='ffill')` and `fillna(method='bfill')` with separate `ffill()` and `bfill()` method calls.

## Empty Output File Issue

**Error**: Script runs successfully but produces CSV with only headers, no data rows.

**Root Cause**: Using intersection of time ranges (max start time, min end time) instead of union when stations have non-overlapping time periods.

**Fix**: Change time range calculation to use `min([df.index.min()])` for start_time and `max([df.index.max()])` for end_time to capture union of all time periods.

## Pandas Reindex Method Deprecation

**Error**: `TypeError: DataFrame.reindex() got an unexpected keyword argument 'method'`

**Root Cause**: The `method` parameter in `reindex()` was also deprecated in newer pandas versions.

**Fix**: Use simpler `resample()` approach with warning suppression instead of complex reindex operations.

## Memory Exhaustion with Large Datasets

**Error**: Script hangs or crashes with out-of-memory errors on large datasets (50+ stations, 2+ years).

**Root Cause**: Creating huge empty DataFrame upfront and filling column by column is memory-intensive.

**Fix**: Process each station individually, then use `pd.concat()` with outer join for memory-efficient merging.

## Data Corruption During Concatenation

**Error**: Temperature values appearing in pressure ranges (1000s instead of 15-25°C).

**Root Cause**: In-place DataFrame modifications during column renaming causing data to get mixed between stations.

**Fix**: Use explicit copying with `df.copy()` and create new DataFrames instead of modifying existing ones in-place.

## Incorrect Missing Data Statistics

**Error**: Missing data percentage shows 0.00% despite visible NaN values in output.

**Root Cause**: Calculating missing data percentage after forward/backward fill operations instead of before.

**Fix**: Calculate missing data statistics before applying gap-filling operations to show true data coverage gaps.
