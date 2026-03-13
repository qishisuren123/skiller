# SKILL: Earth Observation Station Data Merger

## Overview
A Python CLI tool that merges multiple weather station CSV files into a single aligned dataset. The tool resamples data to a common time grid, handles missing values through forward/backward filling, and outputs a unified CSV with flattened column names for multi-station analysis.

## Workflow

1. **Parse CLI Arguments**: Set up argparse with input directory, output file, and resampling frequency parameters
2. **Discover and Load CSV Files**: Scan input directory for CSV files and read each into pandas DataFrames
3. **Standardize Timestamps**: Convert timestamp columns to datetime index and sort chronologically
4. **Create Common Time Grid**: Generate unified time range spanning all stations at specified frequency
5. **Resample and Align**: Resample each station's data to common grid using mean aggregation for upsampling
6. **Handle Missing Values**: Apply forward-fill then backward-fill with 3-step limit to interpolate gaps
7. **Merge and Export**: Concatenate all stations with flattened column names and output summary statistics

## Common Pitfalls

- **Inconsistent timestamp formats**: Solution - Use `pd.to_datetime()` with `infer_datetime_format=True` and handle parsing errors gracefully
- **Memory issues with large datasets**: Solution - Process files in chunks or use `dtype` optimization for numeric columns
- **Duplicate timestamps within stations**: Solution - Group by timestamp and aggregate (mean/median) before resampling
- **Empty or malformed CSV files**: Solution - Validate file structure and skip corrupted files with warning messages
- **Timezone mismatches**: Solution - Standardize all timestamps to UTC using `tz_localize()` or `tz_convert()`

## Error Handling Tips

- Wrap file I/O operations in try-except blocks to catch `FileNotFoundError` and `PermissionError`
- Validate CSV structure before processing (check required columns exist)
- Use `pd.errors.ParserError` to catch malformed CSV files
- Implement logging to track which files fail processing
- Provide meaningful error messages with file names and line numbers when possible

## Reference Code Snippet

```python
import pandas as pd
import argparse
from pathlib import Path

def merge_stations(input_dir, output_file, freq='1h'):
    # Load and process all CSV files
    station_data = []
    for csv_file in Path(input_dir).glob('*.csv'):
        try:
            df = pd.read_csv(csv_file)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            df.sort_index(inplace=True)
            
            # Resample to common frequency
            df_resampled = df.resample(freq).mean()
            
            # Handle missing values
            df_filled = df_resampled.fillna(method='ffill', limit=3)
            df_filled = df_filled.fillna(method='bfill', limit=3)
            
            # Flatten column names with station_id
            station_id = df['station_id'].iloc[0]
            df_filled.columns = [f"{station_id}_{col}" for col in df_filled.columns if col != 'station_id']
            
            station_data.append(df_filled)
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Merge all stations
    merged_df = pd.concat(station_data, axis=1)
    merged_df.to_csv(output_file)
    
    return merged_df
```