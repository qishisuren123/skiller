# Mark-Recapture Population Estimation

Create a CLI script that estimates wildlife population sizes using mark-recapture data. This classic ecological method involves capturing animals, marking them, releasing them, then recapturing a sample later to estimate the total population.

Your script should implement the Lincoln-Petersen estimator, which calculates population size as N = (M × C) / R, where:
- M = number of animals marked in first capture
- C = total number of animals captured in second sample
- R = number of marked animals recaptured in second sample

## Arguments
- `--input`: JSON file containing mark-recapture data
- `--output`: Output JSON file for results
- `--confidence`: Confidence level for intervals (default: 0.95)
- `--method`: Estimation method, either "lincoln" or "chapman" (default: "lincoln")

## Requirements

1. **Parse mark-recapture data** from input JSON containing arrays of capture session data with fields: session_id, marked_count, total_captured, recaptured_count.

2. **Calculate population estimates** using the Lincoln-Petersen estimator (N = M×C/R) for each capture session pair. For Chapman method, use the bias-corrected formula: N = ((M+1)×(C+1)/(R+1)) - 1.

3. **Compute confidence intervals** using the normal approximation method. Calculate standard error as SE = sqrt((M×C×(M-R)×(C-R))/(R³)) and apply the specified confidence level.

4. **Handle edge cases** gracefully: skip sessions where R=0 (no recaptures), warn about small sample sizes (R<5), and validate that recaptured count doesn't exceed marked or total captured counts.

5. **Generate summary statistics** including mean population estimate, coefficient of variation, and data quality metrics (number of valid sessions, average recapture rate).

6. **Output results** as JSON with population estimates, confidence intervals, summary statistics, and metadata about the analysis method and parameters used.
