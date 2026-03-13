# Earthquake Catalog Analysis and Aftershock Sequence Identification

## Overview
This skill helps create a robust Python CLI script for analyzing earthquake catalogs, calculating seismic parameters (b-values), and identifying aftershock sequences. It handles common data format issues, implements proper statistical methods, and provides comprehensive error handling.

## Workflow
1. **Setup argument parsing** with required parameters (input file, output directory) and optional clustering parameters
2. **Validate input data** by checking for required columns and handling different datetime column naming conventions
3. **Load and preprocess data** with proper datetime parsing and sorting
4. **Calculate b-value** using the Aki formula with sophisticated completeness magnitude estimation via linear regression
5. **Identify aftershock sequences** using spatiotemporal clustering while preventing events from being both mainshocks and aftershocks
6. **Generate magnitude-frequency statistics** with proper reverse cumulative distribution calculation
7. **Output results** in multiple formats (JSON for stats, CSV for sequences and frequency data)

## Common Pitfalls
- **Division by zero in b-value calculation**: Occurs when all magnitudes are identical or when variance is zero in regression analysis. Always check denominators before division.
- **Incorrect datetime column handling**: Input files may use different column names. Check multiple variants and provide clear error messages.
- **Faulty cumulative distribution calculation**: Using `np.cumsum(hist[::-1])[::-1]` doesn't give correct reverse cumulative. Use explicit summation from each bin to the end.
- **Events being both mainshocks and aftershocks**: Process mainshocks by decreasing magnitude and track used events to prevent double classification.
- **Poor completeness magnitude estimation**: Simple histogram maximum is inadequate. Use linear regression to find where Gutenberg-Richter law best applies.

## Error Handling
- **File loading errors**: Wrap CSV reading in try-catch and provide informative error messages
- **Missing columns**: Validate all required columns exist before processing
- **Mathematical edge cases**: Check for zero variance, division by zero, and insufficient data points
- **Empty datasets**: Ensure minimum data requirements are met for statistical calculations
- **Invalid regression fits**: Require minimum R² values and fallback to simpler methods when sophisticated approaches fail

## Quick Reference
