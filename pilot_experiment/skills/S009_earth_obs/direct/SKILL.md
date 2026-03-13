# Earth Observation Station Data Merger

## Overview
This skill enables merging and temporal alignment of multiple weather station CSV files into a unified dataset with consistent time sampling and standardized column naming for multi-station analysis.

## Workflow
1. Parse command-line arguments for input directory, output file, and resampling frequency
2. Discover and validate all CSV files in the input directory, checking for required columns
3. Load each station's data with proper datetime parsing and station identification
4. Establish a common time grid spanning all stations at the specified frequency
5. Resample each station's data to the common grid using appropriate aggregation methods
6. Apply missing value imputation (forward-fill then backward-fill with limit=3)
7. Merge all station datasets with standardized column naming and export results

## Common Pitfalls
- **Timezone inconsistencies**: Station timestamps may be in different timezones. Solution: Convert all timestamps to UTC using `pd.to_datetime()` with `utc=True` parameter
- **Irregular sampling intervals**: Raw station data often has gaps or irregular timing. Solution: Use `resample()` with `mean()` for downsampling and proper interpolation for upsampling
- **Memory issues with large datasets**: Loading all stations simultaneously can exhaust memory. Solution: Process stations iteratively and use `pd.concat()` with `join='outer'` for efficient merging
- **Invalid resampling frequencies**: User-provided frequency strings may be malformed. Solution: Validate frequency using `pd.Timedelta()` and provide clear error messages
- **Duplicate timestamps within stations**: Some CSV files may contain duplicate entries. Solution: Use `drop_duplicates()` on timestamp column before resampling

## Error Handling
- Validate input directory exists and contains CSV files before processing
- Check each CSV for required columns (timestamp, temperature, humidity, pressure, station_id)
- Handle malformed datetime strings with `errors='coerce'` and report problematic files
- Catch pandas resampling errors and provide meaningful feedback about frequency format
- Implement file I/O error handling with specific messages for permission and disk space issues

## Quick Reference
