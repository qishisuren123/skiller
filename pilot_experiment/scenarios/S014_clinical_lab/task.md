Write a Python CLI script to normalize and flag clinical laboratory test results.

Input: A CSV with columns: patient_id, test_name, value, unit, reference_low, reference_high, timestamp.

Requirements:
1. Use argparse: --input CSV, --output CSV, --flag-output JSON
2. Normalize values: convert all units to SI standard (mg/dL glucose → mmol/L, multiply by 0.0555; mg/dL creatinine → μmol/L, multiply by 88.4)
3. Flag abnormal results: "low" if value < reference_low, "high" if value > reference_high, "normal" otherwise
4. For each patient, compute: number of abnormal results, most recent test date, critical flags (>2x reference)
5. Output normalized CSV with added columns: normalized_value, flag, is_critical
6. Output flag summary JSON: {patient_id: {n_abnormal, n_critical, tests: [...]}}
7. Print: total patients, abnormal rate, critical rate
