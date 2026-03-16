## CSV Writing Performance Issue

**Error**: Script becomes extremely slow when writing large datasets to CSV format, creating massive files that take minutes to write.

**Root Cause**: The CSV writer processes each row individually and large grids (2000x4000) result in millions of data points being written sequentially.

**Fix**: Added `--skip-csv` command-line flag to bypass CSV output entirely for large datasets, focusing on JSON statistics which are much faster to write.

## NaN Values Breaking Analysis

**Error**: When input SST data contains NaN values (common for land areas or cloud cover), the entire analysis returns NaN results making statistics meaningless.

**Root Cause**: Standard numpy functions like `mean()`, `std()`, `max()`, `min()` propagate NaN values through calculations.

**Fix**: Replaced all statistical functions with NaN-aware versions (`np.nanmean()`, `np.nanstd()`, `np.nanmax()`, `np.nanmin()`) and added data coverage reporting.

## Uniform Field Argmax Error

**Error**: `ValueError: attempt to get argmax of an empty sequence` when processing datasets with identical temperature values across the entire grid.

**Root Cause**: When all temperatures are identical, anomalies become all zeros, and `np.nanargmax()` fails to find a maximum value.

**Fix**: Added try-except block around extreme location finding and provide default [0,0] locations with warning message for uniform fields.
