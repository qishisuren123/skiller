# Disease Outbreak Epidemic Analysis

## Overview
This skill enables analysis of disease outbreak case report data to compute key epidemiological metrics including R0 estimation, epidemic curve generation, case fatality rates by demographics, and outbreak timeline analysis.

## Workflow
1. Parse command-line arguments for input CSV, output directory, and serial interval parameter
2. Load and validate case report data, ensuring proper date parsing and data integrity
3. Generate epidemic curve by aggregating daily case counts from onset dates
4. Identify early growth phase (first 30% of outbreak duration) and fit exponential model to estimate growth rate
5. Calculate R0 using exponential growth method: R0 = 1 + r * serial_interval
6. Compute demographic-specific case fatality rates and location-based attack rates
7. Export results as CSV (epidemic curve) and JSON (summary statistics) with console output

## Common Pitfalls
- **Date parsing errors**: Use pandas.to_datetime() with error handling for malformed dates; filter out invalid entries rather than failing
- **Insufficient early growth data**: Check that early growth phase has at least 5 data points; if not, extend to minimum viable period or warn user
- **Zero/negative case counts**: Handle days with zero cases in log transformation by adding small constant (1) to avoid log(0) errors
- **Missing demographic data**: Use .fillna() to handle missing age/gender/outcome data; exclude from specific calculations but include in totals
- **Linear regression on log scale**: Ensure cumulative cases are monotonically increasing; use np.maximum.accumulate() to enforce this constraint

## Error Handling
- Validate CSV columns exist and have expected data types before processing
- Use try-except blocks around date parsing and numerical computations with informative error messages
- Check for minimum data requirements (at least 10 cases) before attempting R0 estimation
- Handle division by zero in CFR calculations when age groups have zero deaths or cases

## Quick Reference
