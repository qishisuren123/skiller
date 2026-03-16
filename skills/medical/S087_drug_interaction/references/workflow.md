1. Prepare prescription data in CSV format with columns: patient_id, drug_name, dosage, prescription_date
2. Run the analyzer with basic command: `python scripts/main.py prescription_data.csv`
3. Specify output directory: `python scripts/main.py data.csv --output-dir results/`
4. Customize time window for concurrent medications: `--window-days 45`
5. Adjust severity scoring: `--severe-score 5 --moderate-score 3 --minor-score 1`
6. Filter high-risk patients: `--risk-threshold 6`
7. Review generated reports: interactions.csv, risk_distribution.png, high_risk_patients.json
8. Analyze drug name mappings in logs to verify brand-to-generic conversions
9. Examine summary statistics for interaction patterns and common drug pairs
10. Use high-risk patient report for targeted clinical interventions
