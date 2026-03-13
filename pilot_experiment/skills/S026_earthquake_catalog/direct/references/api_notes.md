# Key Libraries and Functions

## pandas
- `pd.read_csv(filepath)` - Load earthquake catalog
- `pd.to_datetime(series)` - Parse datetime strings with automatic format detection
- `df.sort_values('column')` - Sort by datetime for temporal analysis
- `df.between(low, high)` - Validate coordinate ranges
- `df.to_csv(filepath, index=False)` - Export results

## numpy
- `np.histogram(data, bins)` - Create magnitude-frequency distributions
- `np.arange(start, stop, step)` - Generate magnitude bins
- `np.cumsum(array[::-1])[::-1]` - Reverse cumulative sum for frequency analysis
- `np.log10(array)` - Logarithmic transformation for Gutenberg-Richter plots
- `np.maximum(array, value)` - Avoid log(0) errors in cumulative calculations

## math (Haversine distance)
- `radians(degrees)` - Convert coordinates to radians
- `sin(), cos(), sqrt(), atan2()` - Trigonometric functions for great circle distance
- Standard Earth radius: 6371.0 km

## datetime
- `timedelta(hours=n)` - Time window calculations for aftershock identification
- `(datetime2 - datetime1).total_seconds()` - Time difference in seconds

## argparse
- `add_argument('--name', type=float, default=value)` - Numerical parameters
- `add_argument('--input', required=True)` - Required file paths
