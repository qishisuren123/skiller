Write a Python CLI script to analyze daily streamflow records and perform flood frequency analysis.

Input: A CSV file with columns:
- date (YYYY-MM-DD), discharge_cms (cubic meters per second), station_id

Requirements:
1. Use argparse: --input CSV path, --output directory, --return-periods (default "10,50,100" years)
2. Extract annual maximum discharge for each station (water year: Oct-Sep or calendar year)
3. Fit a Generalized Extreme Value (GEV) distribution to annual maxima using scipy.stats.genextreme. Estimate location, scale, shape parameters.
4. Compute flood discharge for specified return periods: Q_T = GEV.ppf(1 - 1/T) where T is return period in years
5. Perform baseflow separation using a simple digital filter: baseflow(t) = alpha * baseflow(t-1) + (1-alpha)/2 * (Q(t) + Q(t-1)) with alpha=0.925, then clip baseflow <= Q
6. Output: annual_maxima.csv (station_id, year, max_discharge), flood_frequency.json (per station: gev_params {shape, loc, scale}, return_periods {T: Q_T}), baseflow.csv (date, station_id, discharge_cms, baseflow_cms, quickflow_cms)
7. Print summary: number of stations, years of record, estimated 100-year flood per station
