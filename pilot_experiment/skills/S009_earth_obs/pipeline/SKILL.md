# Weather Station CSV Merging and Time Alignment

## Overview
This skill helps merge multiple weather station CSV files into a single time-aligned dataset with proper resampling, handling mixed station IDs, duplicate data, and various edge cases like empty files and invalid timestamps.

## Workflow
1. **Validate input frequency format** - Convert user-friendly formats (30min, 1h) to pandas-compatible formats (30T, 1H)
2. **Process CSV files robustly** - Handle empty files, missing columns, and invalid data with proper error reporting
3. **Group data by station ID** - Handle files with mixed station IDs by separating data per station
4. **Establish common time grid** - Find overall time range across all stations for unified alignment
5. **Resample to common frequency** - Align all stations to the same time grid using specified frequency
6. **Merge and fill missing values** - Concatenate aligned data and handle gaps with forward/backward fill
7. **Generate summary statistics** - Report number of stations, time range, and missing data percentage

## Common Pitfalls
- **Duplicate column names**: When concatenating dataframes with same column names from different stations - solve by prefixing columns with station_id
- **Mixed station IDs in files**: Assuming one station per file when files contain multiple stations - solve by grouping data by station_id first
- **Deprecated fillna syntax**: Using `fillna(method='ffill')` in newer pandas versions - use `ffill()` and `bfill()` instead
- **Invalid frequency formats**: User-friendly formats like "30min" not recognized - implement frequency validation and conversion
- **Time grid misalignment**: Each station resampled to its own time range - establish common time grid before resampling
- **Empty/invalid files**: Script crashes on empty files or missing columns - add comprehensive error handling with graceful skipping

## Error Handling
- Check for empty CSV files and skip with warnings
- Validate required columns exist before processing
- Handle timestamp parsing errors gracefully
- Skip rows with invalid/empty station IDs
- Filter to numeric columns only for weather data
- Provide informative error messages and continue processing valid files
- Exit gracefully if no valid data found

## Quick Reference
