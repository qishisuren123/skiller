# xarray - NetCDF data handling
ds = xr.open_dataset(filename)  # Load NetCDF file
ds['variable_name'].values     # Extract numpy array from DataArray

# numpy - Array operations
np.floor(array / resolution) * resolution  # Align to grid boundaries
np.arange(start, end, step)                # Create coordinate arrays
np.where(condition, true_val, false_val)   # Conditional array operations
np.percentile(array, [25, 75])            # Calculate quartiles for outlier detection

# collections.defaultdict - Efficient grouping
from collections import defaultdict
grid_data = defaultdict(list)              # Auto-creates empty lists for new keys

# pandas - Data output
df = pd.DataFrame(results)                 # Create DataFrame from list of dicts
df.to_csv(filename, index=False)          # Export to CSV without row indices

# argparse - CLI interface
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--param', type=float, default=0.25, help='...')
args = parser.parse_args()
