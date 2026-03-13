# Pandas DataFrame Operations
df.groupby('column').agg({'col1': 'sum', 'col2': 'nunique'})  # Group and aggregate
pd.concat([df1, df2])  # Concatenate DataFrames
df.map(lambda x: mapping_dict.get(x, default))  # Apply mapping with fallback
pd.to_datetime(series, errors='coerce')  # Parse timestamps with error handling

# Series Operations for Influence Metrics
series.sort_values(ascending=False)  # Sort for rankings
(series - series.min()) / (series.max() - series.min())  # Min-max normalization
series1.index.intersection(series2.index)  # Find common indices
series.loc[index_list]  # Select by index positions

# JSON Handling for Results Export
json.dump(data, file, indent=2)  # Pretty-print JSON output
datetime.now().isoformat()  # ISO timestamp for analysis metadata

# NumPy for Numerical Operations
np.round(array, decimals=4)  # Round floating point results
float(numpy_scalar)  # Convert numpy types for JSON serialization
