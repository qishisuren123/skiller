---
name: air_quality_index
description: "Write a Python CLI script to compute Air Quality Index (AQI) from hourly pollutant measurements using EPA breakpoints, generate daily AQI values, monthly summaries, and exceedance reports."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: environmental
---

# Air Quality Index Calculator

## Overview
This skill creates a comprehensive Python CLI tool for calculating Air Quality Index (AQI) from hourly pollutant measurements. The tool processes CSV data containing PM2.5, PM10, O3, NO2, SO2, and CO measurements, applies EPA AQI breakpoints with appropriate averaging periods, and generates daily AQI values, monthly summaries, and exceedance reports.

## When to Use
- Processing air quality monitoring data from environmental sensors
- Generating regulatory compliance reports for air quality standards
- Creating public health advisories based on pollutant concentrations
- Analyzing long-term air quality trends and patterns
- Converting raw pollutant measurements to standardized AQI values

## Inputs
- CSV file with columns: timestamp (YYYY-MM-DD HH:MM:SS), pm25 (µg/m³), pm10 (µg/m³), o3 (ppb), no2 (ppb), so2 (ppb), co (ppm)
- Output directory path for generated reports
- Hourly measurements with sufficient data coverage (75% minimum for daily averages)

## Workflow
1. Execute `scripts/main.py` with input CSV and output directory arguments
2. Script reads hourly pollutant data and validates timestamp format
3. Calculates appropriate averaging periods: 24-hour for PM2.5/PM10, 8-hour max for O3/CO, 1-hour max for NO2/SO2
4. Applies EPA AQI breakpoints using linear interpolation to compute sub-indices
5. Determines overall daily AQI as maximum of all valid sub-indices
6. Generates three output files: daily_aqi.csv, monthly_summary.json, exceedance_report.json
7. Consult `references/pitfalls.md` for common data quality and processing issues

## Error Handling
The script includes comprehensive error handling for missing data scenarios. When all sub-indices return NaN due to insufficient data coverage, the system gracefully handles empty sequences and logs warnings. Date format errors are handled by converting between date and datetime objects as needed for different processing stages.

## Common Pitfalls
- Insufficient hourly data coverage causing all sub-indices to be NaN
- Date format mismatches between date objects and datetime operations
- Missing or incorrectly named CSV columns
- Pollutant concentrations outside expected ranges
- Rolling window calculations failing with sparse data

## Output Format
- daily_aqi.csv: Date, AQI value, category, dominant pollutant, individual sub-indices
- monthly_summary.json: Mean/max AQI, category counts, dominant pollutant frequencies by month
- exceedance_report.json: Total days, exceedance count/rate, specific dates, worst day details
- Console output: Summary statistics including mean AQI, exceedance rate, worst day
