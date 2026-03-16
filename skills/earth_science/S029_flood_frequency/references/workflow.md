1. Prepare input CSV file with columns: date, discharge_cms, station_id
2. Run the script: `python scripts/main.py --input data.csv --output results/`
3. Script loads and validates streamflow data, removing invalid values
4. Extract annual maxima using water year (October 1 - September 30)
5. Fit GEV distributions to annual maxima for each station
6. Calculate return period flows for specified intervals (default: 10, 50, 100 years)
7. Perform baseflow separation using digital filter algorithm
8. Save results to three output files:
   - annual_maxima.csv: Annual maximum flows by station and year
   - flood_frequency.json: GEV parameters and return period flows
   - baseflow.csv: Daily flows with baseflow and quickflow components
9. Review console output for summary statistics and warnings
10. Check references/pitfalls.md for troubleshooting common issues
