---
name: earth_obs
description: "Write a Python CLI script to merge and align multiple Earth observation station CSV files into a single dataset.

Input: A directory containing CSV files, each from a different weather station. Each CSV has columns: timestamp, temperature, humidity, pressure, station_id.

Output: A single merged CSV file with all stations aligned to a common time grid, with station-prefixed column names."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: earth_science
---

# Earth Obs

## Overview
This skill provides a robust Python CLI tool for merging and aligning multiple Earth observation station CSV files into a unified dataset. The tool handles different time coverage periods across stations, resamples data to a common frequency, and manages missing data through forward/backward filling techniques.

## When to Use
- Merging weather station data from multiple locations
- Aligning time series data with different sampling frequencies
- Creating unified datasets from distributed sensor networks
- Processing large-scale environmental monitoring data
- Handling datasets with gaps and missing values

## Inputs
- `--input-dir`: Directory containing CSV files from different stations
- `--output`: Path for the merged output CSV file  
- `--freq`: Resampling frequency (default: '1H' for hourly)

Each input CSV must contain: timestamp, temperature, humidity, pressure, station_id columns.

## Workflow
1. Execute `scripts/main.py` with required arguments
2. Script validates input directory and CSV file structure
3. Reads and parses timestamp columns for each station
4. Determines union of all time ranges across stations
5. Resamples each station's data to common frequency grid
6. Merges stations using memory-efficient concatenation
7. Applies forward/backward fill to handle missing values
8. Outputs merged dataset with station-prefixed columns
9. Provides statistics on missing data before/after processing

Refer to `references/workflow.md` for detailed step-by-step instructions.

## Error Handling
The script includes comprehensive error handling for common issues:
- Missing or empty input directories
- Malformed CSV files with missing required columns
- Invalid timestamp formats that cannot be parsed
- Memory issues with large datasets through chunked processing
- Pandas version compatibility (handles deprecated fillna methods)
- Data corruption prevention through explicit copying operations

## Common Pitfalls
- Using deprecated pandas methods (fillna with method parameter)
- Memory exhaustion with large datasets due to inefficient merging
- Data corruption from in-place DataFrame modifications
- Missing data calculations performed after gap-filling operations
- Intersection vs union time range calculations causing empty outputs

See `references/pitfalls.md` for detailed error scenarios and solutions.

## Output Format
Merged CSV file with:
- Timestamp index covering full time range of all stations
- Columns named as `{station_id}_{measurement}` (e.g., "STATION1_temperature")
- Missing values filled using forward/backward propagation (limited to 3 steps)
- Console output showing processing statistics and data quality metrics
