# pandas DataFrame operations
df.groupby('field_id').agg({
    'column': 'first',    # Take first value
    'column': 'last',     # Take last value (good for time series)
    'column': 'sum',      # Sum all values
    'column': 'mean'      # Average all values
})

# NaN handling
df['column'].isna()           # Check for NaN values
df['column'].dropna()         # Remove NaN values
df.dropna(subset=['col'])     # Drop rows with NaN in specific columns
np.where(condition, val_if_true, val_if_false)  # Conditional assignment

# argparse setup
parser = argparse.ArgumentParser(description='Script description')
parser.add_argument('--input', required=True, help='Input file path')
parser.add_argument('--base-temp', type=float, default=10.0, help='Base temperature')

# File operations
os.makedirs(path, exist_ok=True)  # Create directory if not exists
pd.read_csv(path)                 # Load CSV
df.to_csv(path, index=False)      # Save CSV without index
