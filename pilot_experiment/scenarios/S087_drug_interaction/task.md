# Drug Interaction Analysis Tool

Create a CLI script that analyzes prescription data to identify potential drug interactions and generate safety reports.

Your script should accept prescription data containing patient IDs, drug names, dosages, and prescription dates, then cross-reference this against a drug interaction database to identify potentially dangerous combinations.

## Requirements

1. **Data Processing**: Parse prescription records and group by patient to identify concurrent medications (prescribed within a 30-day window).

2. **Interaction Detection**: Implement a drug interaction checker that identifies pairs of medications with known interactions. Consider three severity levels: minor, moderate, and severe.

3. **Risk Scoring**: Calculate a patient risk score based on the number and severity of interactions (severe=3 points, moderate=2 points, minor=1 point).

4. **Statistical Analysis**: Generate summary statistics including total interactions by severity, most common interacting drug pairs, and patient risk distribution.

5. **Output Generation**: Create a detailed JSON report containing patient-level interactions and summary statistics, plus a CSV file listing all detected interactions with patient IDs, drug pairs, severity levels, and dates.

6. **Visualization**: Generate a histogram showing the distribution of patient risk scores and save as PNG.

## Command Line Interface
