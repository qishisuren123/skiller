Write a Python CLI script to compute Air Quality Index (AQI) from hourly pollutant measurements.

Input: A CSV file with columns: timestamp (YYYY-MM-DD HH:MM:SS), pm25 (µg/m³), pm10 (µg/m³), o3 (ppb), no2 (ppb), so2 (ppb), co (ppm).

Requirements:
1. Use argparse: --input CSV path, --output directory
2. Compute the sub-index for each pollutant using US EPA AQI breakpoints:
   - PM2.5 (24-hr avg): [0,12.0]=Good(0-50), [12.1,35.4]=Moderate(51-100), [35.5,55.4]=Unhealthy-SG(101-150), [55.5,150.4]=Unhealthy(151-200), [150.5,250.4]=Very-Unhealthy(201-300), [250.5,500.4]=Hazardous(301-500)
   - PM10 (24-hr avg): [0,54]=Good(0-50), [55,154]=Moderate(51-100), [155,254]=Unhealthy-SG(101-150), [255,354]=Unhealthy(151-200), [355,424]=Very-Unhealthy(201-300), [425,604]=Hazardous(301-500)
   - O3 (8-hr avg): [0,54]=Good(0-50), [55,70]=Moderate(51-100), [71,85]=Unhealthy-SG(101-150), [86,105]=Unhealthy(151-200), [106,200]=Very-Unhealthy(201-300)
   - NO2 (1-hr): [0,53]=Good(0-50), [54,100]=Moderate(51-100), [101,360]=Unhealthy-SG(101-150), [361,649]=Unhealthy(151-200), [650,1249]=Very-Unhealthy(201-300), [1250,2049]=Hazardous(301-500)
   - SO2 (1-hr): [0,35]=Good(0-50), [36,75]=Moderate(51-100), [76,185]=Unhealthy-SG(101-150), [186,304]=Unhealthy(151-200), [305,604]=Very-Unhealthy(201-300), [605,1004]=Hazardous(301-500)
   - CO (8-hr avg): [0,4.4]=Good(0-50), [4.5,9.4]=Moderate(51-100), [9.5,12.4]=Unhealthy-SG(101-150), [12.5,15.4]=Unhealthy(151-200), [15.5,30.4]=Very-Unhealthy(201-300), [30.5,50.4]=Hazardous(301-500)
3. The daily AQI = max of all pollutant sub-indices. The dominant pollutant = the one with the highest sub-index.
4. Compute AQI category: Good (0-50), Moderate (51-100), Unhealthy for Sensitive Groups (101-150), Unhealthy (151-200), Very Unhealthy (201-300), Hazardous (301-500)
5. Aggregate monthly: mean AQI, max AQI, number of days in each category, dominant pollutant frequency
6. Count exceedance days: days where AQI > 100
7. Output files:
   - daily_aqi.csv: date, aqi, category, dominant_pollutant, pm25_aqi, pm10_aqi, o3_aqi, no2_aqi, so2_aqi, co_aqi
   - monthly_summary.json: {month: {mean_aqi, max_aqi, category_counts, dominant_pollutant_counts}}
   - exceedance_report.json: {total_days, exceedance_days, exceedance_rate, exceedance_dates, worst_day, worst_aqi}
8. Print: total days, mean AQI, exceedance rate, worst day
