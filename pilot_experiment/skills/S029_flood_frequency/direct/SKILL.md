# Streamflow Flood Frequency Analysis

## Overview
This skill enables hydrological analysis of daily streamflow records to perform flood frequency analysis using Generalized Extreme Value (GEV) distribution fitting, baseflow separation, and return period calculations for water resources engineering applications.

## Workflow
1. **Parse CLI arguments** - Set up argparse for input CSV, output directory, and return periods with proper validation
2. **Load and validate streamflow data** - Read CSV with date parsing, check required columns, and group by station_id
3. **Extract annual maxima** - Determine water year boundaries (Oct-Sep) and find maximum discharge for each station-year combination
4. **Fit GEV distribution** - Use scipy.stats.genextreme to estimate shape, location, and scale parameters for each station's annual maxima series
5. **Calculate return period discharges** - Apply inverse CDF (ppf) with exceedance probability 1-1/T for specified return periods
6. **Perform baseflow separation** - Implement digital filter algorithm with alpha=0.925 and compute quickflow as total minus baseflow
7. **Export results** - Save annual maxima CSV, flood frequency JSON with GEV parameters, baseflow CSV, and print station summary

## Common Pitfalls
- **Insufficient data for GEV fitting** - Require minimum 10 years of annual maxima; skip stations with inadequate records and warn user
- **Water year boundary errors** - Correctly handle Oct 1 to Sep 30 water years, ensuring year assignment matches the ending calendar year
- **Baseflow filter initialization** - Initialize first baseflow value as first discharge value to prevent numerical instability in recursive filter
- **GEV convergence issues** - Catch scipy optimization failures during parameter estimation and use method of moments as fallback
- **Date parsing inconsistencies** - Use pandas.to_datetime with explicit format and handle missing/invalid dates gracefully

## Error Handling
- Wrap GEV fitting in try-except blocks to handle convergence failures and data quality issues
- Validate that discharge values are positive and finite before analysis
- Check for sufficient data coverage (minimum years) before attempting statistical analysis
- Handle missing dates in time series and ensure continuous daily records for baseflow separation

## Quick Reference
