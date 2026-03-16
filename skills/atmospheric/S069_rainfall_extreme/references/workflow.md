1. Prepare daily precipitation data as comma-separated values
2. Run script with: python scripts/main.py --input-data "1.2,0.0,15.3,..." --output results.json --start-year 2020
3. Script parses input data, handling whitespace and formatting issues robustly
4. Groups precipitation data by calendar year
5. Extracts annual maximum precipitation for each complete year (≥300 days of data)
6. Calculates return periods using Weibull plotting position: RP = (n+1)/rank
7. Sorts data by return period for interpolation/extrapolation
8. Calculates 10-year return period threshold using linear interpolation or extrapolation
9. Identifies all daily precipitation events exceeding the calculated threshold
10. Computes summary statistics including mean/std of annual maxima
11. Exports comprehensive results to JSON file with all components
12. Displays summary information including threshold value and event count
