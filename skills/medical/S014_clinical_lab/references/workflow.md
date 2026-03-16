1. Prepare input CSV file with columns: patient_id, test_name, value, unit, reference_low, reference_high, timestamp
2. Run the script: python scripts/main.py --input lab_data.csv --output normalized_results.csv --flag-output patient_summary.json
3. Script reads CSV and converts timestamps to datetime format
4. Logs missing data statistics and unique test types found
5. Performs vectorized normalization of both test values AND reference ranges to SI units
6. Applies case-insensitive substring matching for test names (glucose, creatinine)
7. Flags results as 'normal', 'low', 'high', or 'unknown' using normalized reference ranges
8. Identifies critical values using 2x upper limit or 0.5x lower limit thresholds
9. Groups data by patient and calculates summary statistics efficiently
10. Outputs normalized CSV with additional columns and JSON patient summary
11. Displays overall statistics including abnormal and critical rates
