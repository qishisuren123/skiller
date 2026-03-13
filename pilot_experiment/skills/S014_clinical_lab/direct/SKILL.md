# Clinical Laboratory Test Result Normalization and Flagging

## Overview
This skill helps create a CLI tool for processing clinical laboratory test results by normalizing units to SI standards, flagging abnormal values, and generating summary statistics for patient care monitoring.

## Workflow
1. Parse command line arguments for input CSV, output CSV, and flag summary JSON paths
2. Load and validate the clinical data CSV with required columns (patient_id, test_name, value, unit, reference_low, reference_high, timestamp)
3. Apply unit normalization rules to convert common lab values to SI units (glucose mg/dL → mmol/L, creatinine mg/dL → μmol/L)
4. Flag test results as "low", "normal", or "high" by comparing normalized values against reference ranges
5. Identify critical results (>2x outside reference range) and mark with is_critical flag
6. Generate patient-level summary statistics including abnormal counts, critical counts, and most recent test dates
7. Export normalized results CSV and patient summary JSON, then print overall statistics

## Common Pitfalls
- **Missing unit conversion**: Not all test types have standard conversions - handle unknown units gracefully by keeping original values
- **Reference range validation**: Some CSV rows may have invalid reference ranges (low > high) - validate and skip these records
- **Timestamp parsing errors**: Clinical timestamps can be in various formats - use pandas' flexible date parsing with error handling
- **Division by zero in flagging**: Reference ranges of zero will cause calculation errors - add checks before computing critical thresholds
- **Memory issues with large datasets**: Clinical datasets can be massive - process in chunks if memory becomes an issue

## Error Handling
- Validate all required columns exist before processing
- Use try-except blocks around unit conversions to handle unexpected test types
- Check for null/NaN values in critical columns and either skip or impute appropriately
- Wrap file I/O operations in error handling for permission and path issues

## Quick Reference
