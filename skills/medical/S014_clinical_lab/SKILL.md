---
name: clinical_lab
description: "Write a Python CLI script to normalize and flag clinical laboratory test results.

Input: A CSV with columns: patient_id, test_name, value, unit, reference_low, reference_high, timestamp.

Requirement"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: medical
---

# Clinical Lab

## Overview
This skill creates a Python CLI script to process clinical laboratory test results. It normalizes values to SI units, flags abnormal results, identifies critical values, and generates patient summaries. The script handles missing data gracefully and uses vectorized operations for high performance with large datasets.

## When to Use
- Processing clinical lab data from CSV files
- Converting lab values to standardized SI units
- Flagging abnormal and critical lab results
- Generating patient-level summaries of lab findings
- Quality control and analysis of laboratory datasets

## Inputs
- CSV file with columns: patient_id, test_name, value, unit, reference_low, reference_high, timestamp
- Test values may contain missing data (NaN)
- Test names can vary in case and format (e.g., "Glucose", "GLUCOSE", "Blood Glucose")
- Units should be specified for proper conversion

## Workflow
1. Use scripts/main.py to process the clinical lab data
2. The script reads CSV input and converts timestamps to datetime format
3. Normalizes both test values AND reference ranges to SI units using vectorized operations
4. Flags results as 'normal', 'low', 'high', or 'unknown' (for missing data)
5. Identifies critical values using 2x upper limit or 0.5x lower limit thresholds
6. Generates patient summaries with abnormal/critical counts and most recent test dates
7. Outputs normalized CSV and JSON summary files
8. Refer to references/pitfalls.md for common error patterns and solutions

## Error Handling
The script includes comprehensive error handling for clinical data processing:
- Handles missing values in test results and reference ranges gracefully
- Uses pd.isna() checks to detect and handle NaN values appropriately
- Returns 'unknown' flags when reference ranges are missing
- Implements try-catch patterns for JSON serialization issues
- Validates data types and converts pandas int64 to native Python types

## Common Pitfalls
- JSON serialization errors with pandas data types - convert to native Python types
- Missing value crashes - always check for NaN before comparisons
- Exact string matching failures - use case-insensitive substring matching
- Performance issues with large datasets - use vectorized operations instead of apply()
- Unit conversion bugs - normalize both values AND reference ranges consistently

## Output Format
- Normalized CSV with additional columns: normalized_value, flag, is_critical
- JSON summary file with patient-level statistics including abnormal counts, critical counts, and most recent test dates
- Console output showing overall statistics: total patients, abnormal rate, critical rate
