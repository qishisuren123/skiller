# Atmospheric Visibility Analysis and Fog Frequency Calculator

Create a CLI script that analyzes atmospheric visibility data to compute fog frequency statistics and identify visibility trends. The script should process synthetic visibility measurements and generate comprehensive fog analysis reports.

## Requirements

1. **Data Generation**: Generate synthetic hourly visibility data for a specified number of days, including visibility distance (meters), relative humidity (%), temperature (°C), and wind speed (m/s). Visibility should follow realistic patterns with occasional fog events (visibility < 1000m).

2. **Fog Classification**: Classify visibility conditions into categories: Dense Fog (< 200m), Moderate Fog (200-500m), Light Fog (500-1000m), Mist (1000-5000m), and Clear (> 5000m). Calculate the frequency and duration statistics for each category.

3. **Meteorological Correlation**: Analyze the relationship between fog occurrence and meteorological parameters. Compute correlation coefficients between visibility and humidity, temperature, and wind speed during fog events.

4. **Diurnal Analysis**: Calculate fog frequency by hour of day to identify diurnal patterns. Determine peak fog hours and compute the average fog duration for different time periods (night: 22-06h, morning: 06-12h, afternoon: 12-18h, evening: 18-22h).

5. **Trend Analysis**: Identify visibility trends by computing daily minimum visibility, fog event frequency per day, and longest continuous fog duration. Generate a time series of these metrics.

6. **Output Generation**: Save results to a JSON file containing fog statistics, correlation analysis, diurnal patterns, and trend data. Also generate a CSV file with processed hourly data including fog classifications.

## Command Line Interface
