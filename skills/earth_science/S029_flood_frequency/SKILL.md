---
name: flood_frequency
description: "Write a Python CLI script to analyze daily streamflow records and perform flood frequency analysis.

Input: A CSV file with columns:
- date (YYYY-MM-DD), discharge_cms (cubic meters per second), station_id"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: earth_science
---

# Flood Frequency Analysis

## Overview
This skill creates a comprehensive Python CLI tool for analyzing daily streamflow records and performing flood frequency analysis. The tool extracts annual maxima, fits GEV (Generalized Extreme Value) distributions, calculates return period flows, and performs baseflow separation using digital filters.

## When to Use
- Analyzing historical streamflow data for flood risk assessment
- Calculating design floods for infrastructure projects
- Separating baseflow from surface runoff components
- Estimating return period flows (10-year, 100-year floods)
- Processing multi-station hydrological datasets

## Inputs
- CSV file with columns: date, discharge_cms, station_id
- Return periods (comma-separated, default: 10,50,100 years)
- Output directory path

## Workflow
1. Execute `scripts/main.py` with required arguments
2. Load and validate streamflow data with robust error handling
3. Extract annual maxima using water year (Oct 1 - Sep 30)
4. Fit GEV distributions to annual maxima series
5. Calculate return period flows for specified intervals
6. Perform baseflow separation using digital filter algorithm
7. Save results to CSV and JSON files
8. Reference `references/pitfalls.md` for common data quality issues

## Error Handling
The script includes comprehensive error handling for data quality issues:
- Handles whitespace in column names and missing columns
- Removes negative, infinite, and NaN discharge values
- Validates GEV fitting parameters and handles convergence failures
- Manages insufficient data scenarios gracefully
- Prevents array indexing errors in baseflow separation

## Common Pitfalls
- Column name whitespace causing KeyError exceptions
- Non-finite values in discharge data breaking GEV fitting
- Array indexing errors in digital filter implementation
- Insufficient data points for reliable statistical analysis

## Output Format
- `annual_maxima.csv`: Annual maximum flows by station and year
- `flood_frequency.json`: GEV parameters and return period flows
- `baseflow.csv`: Daily flows with baseflow and quickflow components
- Console summary with key statistics and flood estimates
