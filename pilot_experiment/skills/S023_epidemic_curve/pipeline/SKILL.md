# Disease Outbreak Data Analysis CLI Script

## Overview
This skill helps create a robust Python CLI script for analyzing disease outbreak data from CSV files. It calculates key epidemiological metrics including R0 (basic reproduction number), case fatality rates, epidemic curves, and handles various edge cases and data validation issues.

## Workflow
1. **Set up argument parsing** with required input/output paths and optional parameters
2. **Validate input data structure** checking for required columns and data types
3. **Clean and preprocess data** handling missing values and date conversions
4. **Build epidemic curve** with complete date series including zero-case days
5. **Calculate R0 using exponential growth method** with proper time indexing
6. **Compute additional metrics** (CFR by age groups, case distributions)
7. **Save results** to CSV and JSON files with comprehensive error handling

## Common Pitfalls
- **Zero case logarithm error**: Filter out zero cumulative cases before log transformation
- **Incorrect time indexing**: Preserve original time indices when filtering data, don't use sequential numbering
- **Invalid CFR values >1.0**: Use proper age bin edges with `right=False` parameter in `pd.cut()`
- **Missing required columns**: Validate input file structure before processing
- **Single-day outbreaks**: Check for time variation before attempting exponential fitting
- **Attack rate confusion**: Don't calculate attack rates without population denominators

## Error Handling
- **File validation**: Check file existence and readability
- **Column validation**: Verify all required columns are present
- **Data type validation**: Convert and validate dates, numeric ages, categorical outcomes
- **R0 calculation robustness**: Handle insufficient data points, poor fits (R² < 0.5), and extreme growth ratios
- **Graceful degradation**: Return None for impossible calculations rather than crashing

## Quick Reference
