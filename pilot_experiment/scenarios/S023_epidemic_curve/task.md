Write a Python CLI script to analyze disease outbreak case report data and produce epidemic curve statistics.

Input: A CSV file with columns: case_id, onset_date (YYYY-MM-DD), age, gender (M/F), location, outcome (recovered/deceased/hospitalized).

Requirements:
1. Use argparse: --input CSV, --output directory, --serial-interval (default 5.0 days, mean generation time for R0 estimation)
2. Build an epidemic curve: aggregate daily case counts from onset_date
3. Compute the basic reproduction number R0 using exponential growth rate method:
   - Fit exponential model to the early growth phase (first 30% of total duration)
   - growth_rate r = slope of ln(cumulative_cases) vs time
   - R0 = 1 + r * serial_interval
4. Find peak date (day with maximum new cases) and compute doubling time = ln(2) / r
5. Compute Case Fatality Rate (CFR) by age group: age bins [0-18, 19-40, 41-60, 61+]
6. Output:
   - epi_curve.csv: columns date, daily_cases, cumulative_cases
   - analysis.json: {R0, peak_date, CFR_by_age: {group: rate}, total_cases, doubling_time, growth_rate, attack_rate_by_location}
7. Print: R0 estimate, peak date, overall CFR, total cases
