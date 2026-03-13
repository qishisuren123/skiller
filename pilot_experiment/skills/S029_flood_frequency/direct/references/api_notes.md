# pandas - Data manipulation
pd.read_csv(filepath)                    # Load CSV data
pd.to_datetime(series)                   # Convert to datetime
df.groupby('column').agg(['min', 'max']) # Group and aggregate
df.sort_values(['col1', 'col2'])         # Sort by multiple columns

# scipy.stats.genextreme - GEV distribution
genextreme.fit(data)                     # Fit GEV, returns (shape, loc, scale)
genextreme.ppf(p, shape, loc, scale)     # Percent point function (inverse CDF)

# numpy - Numerical operations
np.zeros_like(array)                     # Create array of zeros with same shape
array.values                             # Extract numpy array from pandas Series

# pathlib.Path - File system operations
Path(directory).mkdir(parents=True, exist_ok=True)  # Create directory structure

# json - JSON file handling
json.dump(data, file, indent=2)          # Write formatted JSON to file
