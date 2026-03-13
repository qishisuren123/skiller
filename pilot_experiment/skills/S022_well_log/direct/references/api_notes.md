# pandas DataFrame operations
df = pd.read_csv(filename)                    # Load CSV data
df.dropna(subset=['col1', 'col2'])           # Remove rows with NaN in specified columns
df.sort_values('column').reset_index(drop=True)  # Sort and reset index
df['new_col'] = df.apply(function, axis=1)   # Apply function to each row
df.to_csv(filename, index=False)             # Save to CSV without row indices

# scipy.interpolate.interp1d
from scipy.interpolate import interp1d
f = interp1d(x, y, kind='linear', bounds_error=False, fill_value=np.nan)
y_new = f(x_new)                             # Interpolate at new x points

# numpy array operations
np.arange(start, stop, step)                 # Create uniform array
np.clip(array, min_val, max_val)             # Clip values to range
array.min(), array.max(), array.mean()      # Basic statistics

# argparse for CLI
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--input', required=True, help='...')
parser.add_argument('--depth-step', type=float, default=0.5)
args = parser.parse_args()
