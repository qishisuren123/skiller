---
name: phenology_shifts
description: "# Phenological Shift Detection Analysis

Create a CLI script that analyzes long-term ecological observation data to detect and quantify phenological shifts - changes in the timing of recurring biological events like migration, flowering, or breeding. Uses PELT changepoint detection, Mann-Kendall trend tests, segmented regression, and climate correlation analysis with proper statistical corrections."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: ecology
---

# Phenology Shifts

## Overview
Analyzes long-term ecological time series data to detect and quantify phenological shifts using advanced statistical methods. Implements PELT (Pruned Exact Linear Time) changepoint detection, Mann-Kendall trend analysis, segmented regression with confidence intervals, and climate correlation analysis with Benjamini-Hochberg multiple comparison correction.

## When to Use
- Analyzing bird migration timing changes over decades
- Detecting shifts in plant flowering or leaf-out dates
- Quantifying breeding season timing changes
- Correlating phenological events with climate variables
- Research requiring robust statistical analysis of ecological time series

## Inputs
- CSV/Excel file with columns: year, doy (day of year), temperature, precipitation
- Flexible column naming (e.g., temp_spring, precip_spring automatically mapped)
- Minimum 10 years of data recommended for reliable changepoint detection
- Missing values handled via interpolation

## Workflow
1. Load and validate data using scripts/main.py with flexible column mapping
2. Preprocess data to handle missing values and flag outliers
3. Run PELT changepoint detection with configurable penalty parameter
4. Perform Mann-Kendall trend test for overall temporal trends
5. Execute segmented regression analysis with confidence intervals
6. Calculate climate correlations with lag analysis (0-3 years)
7. Apply Benjamini-Hochberg correction for multiple comparisons
8. Export results to JSON with statistical summaries
9. Reference references/workflow.md for detailed methodology

## Error Handling
The system includes comprehensive error handling for common data issues. File path errors are handled by converting string inputs to Path objects. Missing or misnamed columns trigger automatic mapping detection. Insufficient data points for statistical tests error out gracefully with informative messages. Changepoint indexing errors are prevented through bounds checking and proper array-to-year conversion.

## Common Pitfalls
- Insufficient data points (< 10 years) leading to unreliable changepoint detection
- Mismatched column names causing validation failures
- Array indexing errors when converting PELT results to actual years
- Multiple comparison issues without proper statistical correction
- Overfitting with too many segments in regression analysis

## Output Format
JSON file containing changepoints (years), Mann-Kendall results (trend, p-value, z-score), segmented regression (slopes, confidence intervals, R²), climate correlations (Pearson/Spearman with lags), and corrected p-values using Benjamini-Hochberg method. Includes data summary statistics and quality metrics.
