# pandas DataFrame operations for time series data
pd.read_csv(filepath)                    # Load CSV with pollutant data
pd.to_datetime(series)                   # Convert timestamp strings
df.set_index('timestamp')                # Set datetime index for resampling
df.rolling(window=8, min_periods=6)      # Rolling window for 8-hour averages
df.groupby(df.index.date)               # Group by calendar date
series.value_counts()                    # Count category occurrences

# numpy operations for AQI calculations  
np.nan                                   # Represent missing/invalid AQI values
pd.isna(value)                          # Check for missing data
series.dropna()                         # Remove NaN values before aggregation
series.mean(), series.max()             # Statistical aggregations

# argparse for CLI interface
parser = argparse.ArgumentParser()       # Create argument parser
parser.add_argument('--input', required=True)  # Required file path argument
args = parser.parse_args()              # Parse command line arguments

# pathlib for file operations
Path(directory).mkdir(parents=True, exist_ok=True)  # Create output directory
