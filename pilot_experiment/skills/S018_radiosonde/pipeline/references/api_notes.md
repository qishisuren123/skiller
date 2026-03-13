# Pandas DataFrame operations for radiosonde data
df.sort_values('altitude')  # Sort by altitude ascending
df.dropna(subset=['pressure', 'temperature', 'altitude'])  # Remove rows with missing critical data
df.iloc[i]['column']  # Access row by position
df[df['altitude'] >= 5000]  # Filter by condition
pd.isna(value)  # Check for NaN values

# NumPy operations
np.nan  # Represent missing values
float(value)  # Convert to float for JSON serialization

# File I/O
pd.read_csv(filepath)  # Read CSV data
df.to_csv(filepath, index=False)  # Write CSV without row indices
json.dump(data, file, indent=2)  # Write formatted JSON
os.makedirs(path, exist_ok=True)  # Create directory if not exists
