1. Prepare input CSV file with columns: timestamp, pm25, pm10, o3, no2, so2, co
2. Run script: python scripts/main.py --input data.csv --output results/
3. Script validates timestamp format and converts to datetime objects
4. For each date, calculate appropriate averaging periods:
   - PM2.5/PM10: 24-hour average (minimum 18 hours of data)
   - O3/CO: 8-hour rolling maximum (minimum 6 periods)
   - NO2/SO2: 1-hour maximum values
5. Apply EPA AQI breakpoints using linear interpolation
6. Compute sub-indices for each pollutant
7. Determine overall AQI as maximum of valid sub-indices
8. Identify dominant pollutant causing highest AQI
9. Generate daily_aqi.csv with all calculated values
10. Create monthly_summary.json with aggregated statistics
11. Generate exceedance_report.json for days with AQI > 100
12. Display summary statistics to console
