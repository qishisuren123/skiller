# Heat Index Analysis and Heat Wave Detection

Create a CLI script that processes atmospheric temperature and humidity data to calculate heat index time series and identify heat wave events with statistical analysis.

Your script should accept the following arguments:
- `--temp-data`: Path to temperature data file (CSV with datetime and temperature columns)
- `--humidity-data`: Path to humidity data file (CSV with datetime and humidity columns)
- `--output-timeseries`: Path for output heat index time series (CSV)
- `--output-heatwaves`: Path for heat wave events output (JSON)
- `--baseline-years`: Number of years to use for baseline climatology (default: 30)
- `--heatwave-threshold`: Percentile threshold for heat wave detection (default: 90)
- `--min-duration`: Minimum duration in days for heat wave classification (default: 3)

## Requirements

1. **Heat Index Calculation**: Implement the full National Weather Service heat index formula including the adjustment factors for low/high humidity conditions. Handle edge cases where the simplified formula is insufficient.

2. **Climatological Baseline**: Calculate a rolling climatological baseline using the specified number of years. For each day of year, compute the percentile threshold from historical data using a 15-day window centered on that day.

3. **Heat Wave Detection**: Identify heat wave events as consecutive periods where daily maximum heat index exceeds the climatological threshold for at least the minimum duration. Merge events separated by single days below threshold.

4. **Statistical Analysis**: For each detected heat wave, calculate: duration, mean/maximum heat index, cumulative excess heat (degree-days above threshold), and return period estimate based on historical frequency.

5. **Temporal Trends**: Compute decadal trends in heat wave frequency, duration, and intensity using linear regression. Include confidence intervals and statistical significance testing.

6. **Output Generation**: Save complete heat index time series with metadata and heat wave events as structured JSON including all calculated statistics, trends, and detection parameters used.

The heat index formula requires careful implementation of the multi-step NWS algorithm with proper handling of temperature/humidity ranges and adjustment factors.
