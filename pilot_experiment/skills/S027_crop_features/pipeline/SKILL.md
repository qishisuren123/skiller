# Python CLI for Crop Yield Prediction Feature Engineering

## Overview
This skill helps create a robust Python CLI script for processing agricultural field observation data and generating crop yield prediction features. It handles data loading, Growing Degree Days (GDD) calculation, NDVI statistics, correlation analysis, and comprehensive error handling for real-world messy data.

## Workflow
1. **Setup argument parsing** with required input/output paths and optional parameters
2. **Load and validate CSV data** with required columns check
3. **Calculate Growing Degree Days (GDD)** with proper NaN handling
4. **Compute NDVI statistics** per field including peak dates
5. **Create feature matrix** with field-level aggregations
6. **Generate correlation matrix** for numeric features
7. **Produce summary statistics** and save all outputs

## Common Pitfalls
- **Duplicate axis error**: Occurs when renaming columns incorrectly in pandas aggregations. Use explicit `rename()` instead of direct column assignment
- **NaN propagation in cumsum()**: Missing temperature values cause NaN to propagate through cumulative calculations. Handle explicitly with `np.where()`
- **Using 'max' vs 'last' for cumulative values**: Use 'last' for time-series cumulative data, not 'max' which can pick anomalous values
- **Missing columns in correlation matrix**: Ensure all calculated features are included in both feature matrix column order and correlation calculation
- **Index issues with idxmax()**: When all values are NaN, `idxmax()` returns NaN which can't be used as index. Always check for valid data first

## Error Handling
- **Data validation**: Check for required columns and data types on load
- **NaN temperature handling**: Treat missing temperature as 0 GDD contribution
- **All-NaN NDVI fields**: Return structured NaN values with 'N/A' strings for dates
- **Field validation**: Identify and report fields with problematic data patterns
- **Graceful degradation**: Continue processing valid fields even when some have issues

## Quick Reference
