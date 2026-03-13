# Flood Frequency Analysis with Python CLI

## Overview
This skill helps create a robust Python CLI script for flood frequency analysis using streamflow data. It covers annual maxima extraction, GEV distribution fitting, baseflow separation using digital filters, and proper error handling for hydrological data analysis.

## Workflow
1. **Setup argument parsing** with argparse for input file, output directory, and return periods
2. **Load and validate CSV data** with pandas, ensuring proper date parsing
3. **Extract annual maxima** using correct water year logic (Oct 1 - Sep 30)
4. **Perform baseflow separation** using digital filter with proper gap handling
5. **Fit GEV distribution** with robust error handling and parameter validation
6. **Calculate flood estimates** for specified return periods with sanity checks
7. **Save results** to CSV and JSON files with comprehensive output

## Common Pitfalls
- **Water year calculation error**: Initially used `>= 10` to add 1 to year, but should add 1 to the year when month >= 10 (Oct-Dec belongs to next water year)
- **Digital filter continuity**: Skipping missing values breaks the recursive filter - must process continuous segments separately
- **GEV fitting failures**: Raw scipy.stats.genextreme.fit() can fail with optimization errors - need robust error handling and fallback methods
- **Unrealistic flood estimates**: GEV extrapolation can produce estimates 10x higher than observed - requires sanity checks and parameter validation
- **Baseflow clipping timing**: Clipping baseflow after calculation rather than integrating it into the recursive process causes oscillation

## Error Handling
- **Missing data handling**: Identify continuous segments and restart digital filter after gaps
- **GEV fitting errors**: Catch FitSolverError and try method of moments as fallback
- **Parameter validation**: Check for positive scale parameters and reasonable shape parameters
- **Data quality checks**: Remove NaN values, negative discharges, and detect extreme outliers
- **Result validation**: Sanity check flood estimates against observed data ratios

## Quick Reference
