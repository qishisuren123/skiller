# Air Quality Index (AQI) Calculator

## Overview
This skill helps create a Python CLI script to compute Air Quality Index (AQI) from hourly pollutant measurements using US EPA breakpoints, with daily aggregation, monthly summaries, and exceedance reporting.

## Workflow
1. Parse command line arguments for input CSV and output directory paths
2. Load and validate hourly pollutant data with proper timestamp parsing
3. Apply temporal averaging rules (24-hr for PM2.5/PM10, 8-hr for O3/CO, 1-hr for NO2/SO2)
4. Calculate sub-indices for each pollutant using EPA AQI breakpoint interpolation
5. Determine daily AQI as maximum sub-index and identify dominant pollutant
6. Generate monthly aggregations with category counts and pollutant frequency statistics
7. Export results to daily CSV, monthly JSON summary, and exceedance report

## Common Pitfalls
- **Averaging period confusion**: PM2.5/PM10 use 24-hour averages, O3/CO use 8-hour rolling max, NO2/SO2 use 1-hour max - mixing these up invalidates AQI calculations
- **Breakpoint interpolation errors**: AQI formula is `((I_hi - I_lo)/(C_hi - C_lo)) * (C - C_lo) + I_lo` where concentration must fall within breakpoint ranges
- **Missing data handling**: Insufficient data for averaging periods should result in NaN AQI, not zero or interpolated values
- **Timestamp timezone issues**: Ensure consistent timezone handling for daily aggregation boundaries
- **Edge case concentrations**: Values exceeding highest breakpoint (>500 AQI) should be handled gracefully

## Error Handling
- Validate CSV columns match expected pollutant names and units
- Check for sufficient data points when computing rolling averages
- Handle missing or invalid concentration values with appropriate NaN propagation
- Verify output directory exists and is writable before processing
- Catch and report breakpoint lookup failures for out-of-range concentrations

## Quick Reference
