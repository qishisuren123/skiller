## CSV Parsing Errors with European Number Formats

**Error**: `ValueError: could not convert string to float: '0.5,1.2'`

**Root Cause**: CSV files using commas as decimal separators instead of dots, or different delimiters (semicolon, tab) common in European locales.

**Fix**: Added fallback CSV parsing with multiple delimiters and string replacement to convert commas to dots before float conversion.

## Memory Crashes with Large Datasets

**Error**: Script hangs and eventually runs out of memory when processing large neural datasets.

**Root Cause**: Loading entire large CSV files into memory at once, creating large intermediate DataFrames during processing.

**Fix**: Implemented chunked data loading with configurable chunk sizes, explicit garbage collection, and memory-efficient processing algorithms.

## Pandas Deprecation Warnings

**Error**: `FutureWarning: The default value of numeric_only in DataFrameGroupBy.mean is deprecated`

**Root Cause**: Pandas version changes requiring explicit specification of numeric_only parameter in groupby operations.

**Fix**: Added `numeric_only=True` parameter to all `.mean()` calls and `skipna=True` for robust handling.

## SEM Calculation Errors with Missing Data

**Error**: `RuntimeError: Degrees of freedom <= 0 for slice` when calculating standard error of mean.

**Root Cause**: Time points with only one trial or NaN values causing scipy.stats.sem to fail.

**Fix**: Created custom `safe_sem()` function that handles edge cases by checking data point count and cleaning NaN values.

## Misleading Population Statistics with Variable Neuron Recording

**Error**: Population PSTH shows unrealistic spikes at certain time points.

**Root Cause**: Trials with different numbers of active neurons causing biased population means when some neurons are silent or not recorded.

**Fix**: Implemented robust population mean calculation requiring minimum number of active neurons per time point, with filtering of insufficient data points.

## Cluttered Heatmap Time Axis

**Error**: Heatmap x-axis shows overlapping time values that are unreadable.

**Root Cause**: Using raw time values as axis labels without proper spacing or binning.

**Fix**: Implemented smart tick spacing showing approximately 10 time points with proper formatting and 45-degree rotation for readability.
