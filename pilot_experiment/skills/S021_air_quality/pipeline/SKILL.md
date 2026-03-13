# Air Quality Index (AQI) Calculation from Hourly Pollutant Data

## Overview
This skill helps create a Python CLI script to calculate EPA Air Quality Index (AQI) values from hourly pollutant measurements. It handles proper averaging periods for different pollutants, calculates daily AQI values, and generates monthly aggregations with comprehensive output files.

## Workflow
1. **Setup Data Structure**: Define EPA AQI breakpoints for all six criteria pollutants (PM2.5, PM10, O3, NO2, SO2, CO)
2. **Read and Parse Input**: Load CSV data with timestamp and pollutant columns, convert timestamps to datetime objects
3. **Apply Correct Averaging Periods**:
   - PM2.5/PM10: 24-hour average
   - O3/CO: 8-hour rolling maximum (minimum 6 hours of data)
   - NO2/SO2: 1-hour maximum
4. **Calculate Individual AQI Values**: Use linear interpolation between EPA breakpoints for each pollutant
5. **Determine Overall Daily AQI**: Take maximum AQI across all pollutants, identify dominant pollutant
6. **Generate Outputs**: Create daily CSV, monthly aggregations, and summary JSON files

## Common Pitfalls
- **Rolling Window Calculation**: Don't use `groupby().rolling().groupby()` - this creates incorrect nested grouping. Instead, sort data first, apply rolling window, then group by date for maximum
- **Data Access from Grouped Series**: Use `.loc[date] if date in series.index else None` instead of `.get(date)` to safely access grouped pandas Series
- **Missing Data Handling**: Check for both `pd.isna()` and `None` values when calculating AQI to avoid errors
- **Output Directory**: Always create output directory with `os.makedirs(path, exist_ok=True)` before writing files
- **Date Serialization**: Convert date objects to strings when writing JSON output to avoid serialization errors

## Error Handling
- Wrap main processing in try-except blocks with detailed error messages
- Add data validation to check for required columns in input CSV
- Handle missing pollutant data gracefully by returning None for AQI calculations
- Use `min_periods` parameter in rolling calculations to handle insufficient data
- Validate AQI breakpoint ranges and provide fallback for values exceeding maximum thresholds

## Quick Reference
