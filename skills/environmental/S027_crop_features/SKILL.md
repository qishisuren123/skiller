---
name: crop_features
description: "Write a Python CLI script to compute crop yield prediction features from field observation data.

Input: A CSV file with columns:
- field_id, date (YYYY-MM-DD), ndvi, soil_moisture, temperature, rainfall_mm"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: environmental
---

# Crop Features

## Overview
This skill creates a Python CLI script to process agricultural field observation data and compute features for crop yield prediction. The script calculates growing degree days (GDD), aggregates NDVI statistics, creates correlation matrices, and generates summary reports. It handles edge cases like single-observation fields and optimizes performance for large datasets.

## When to Use
- Processing agricultural field observation data for yield prediction models
- Computing growing degree days and vegetation index statistics
- Creating feature matrices from time-series field measurements
- Analyzing correlations between environmental factors and crop yields
- Handling large datasets (50,000+ observations) with performance optimization

## Inputs
- CSV file with columns: field_id, date, ndvi, soil_moisture, temperature, rainfall_mm, crop_type, yield_tons
- Base temperature for GDD calculation (default: 10.0°C)
- Output directory path

## Workflow
1. Load and validate input CSV data using pandas
2. Execute scripts/main.py with proper argument parsing and logging
3. Compute growing degree days using vectorized operations
4. Aggregate NDVI statistics per field with NaN handling
5. Create optimized feature matrix using single groupby operations
6. Compute correlation matrix with numpy optimization
7. Generate summary statistics and identify top yield correlates
8. Save outputs: field_features.csv, correlation_matrix.csv, summary.json
9. Reference references/pitfalls.md for common error patterns and fixes

## Error Handling
The script includes comprehensive error handling for common issues. It detects and handles NaN values from single-observation fields by setting standard deviation to 0.0. The correlation computation gracefully handles missing data using pairwise complete observations. Peak NDVI date calculation uses vectorized operations to avoid index mismatch errors. Performance optimization prevents memory issues with large datasets through efficient groupby operations.

## Common Pitfalls
- Peak NDVI date calculation failing due to index mismatches in grouped data
- NaN values in correlation matrix from fields with single observations
- Pandas version compatibility issues with dictionary conversion methods
- Performance degradation with large datasets due to inefficient aggregations
- Broadcasting errors in numpy correlation calculations with wrong array shapes

## Output Format
- field_features.csv: Feature matrix with field_id, crop_type, yield_tons, environmental features
- correlation_matrix.csv: Pearson correlation matrix for all numeric features
- summary.json: Processing statistics including field count, top yield correlates, feature names
