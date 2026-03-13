# Rainfall Return Period Analysis

Create a CLI script that analyzes daily precipitation data to compute rainfall return periods and identify extreme precipitation events.

Your script should accept daily precipitation measurements and calculate return periods using the annual maximum series method. Return periods indicate how frequently extreme rainfall events of a given magnitude are expected to occur.

## Requirements

1. **Data Input**: Accept daily precipitation data via `--input-data` argument as comma-separated values (mm/day). Parse this into a time series assuming consecutive daily measurements starting from a given year.

2. **Annual Maxima Extraction**: Extract the maximum daily precipitation for each complete year in the dataset. Skip incomplete years at the beginning or end of the time series.

3. **Return Period Calculation**: Calculate return periods for the annual maxima using the Weibull plotting position formula: T = (n+1)/r, where n is the number of years and r is the rank (1 for highest value).

4. **Extreme Event Identification**: Identify all daily precipitation events that exceed the 10-year return period threshold. Output these as extreme events with their dates and magnitudes.

5. **Statistical Summary**: Calculate and output basic statistics including mean annual maximum, standard deviation, and the 95th percentile of daily precipitation across the entire dataset.

6. **JSON Output**: Save results to a JSON file specified by `--output` containing: annual maxima values, their corresponding return periods, extreme events list, and statistical summary.

The script should handle edge cases like missing data (represented as negative values) by excluding those days from analysis.

**Usage Example:**
