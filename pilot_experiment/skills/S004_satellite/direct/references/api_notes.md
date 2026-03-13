# NetCDF4 Library
Dataset(filename, mode='r') - Open NetCDF file
nc.variables['var_name'][:] - Read entire variable array
nc.variables.keys() - List available variables

# NumPy Spatial Operations  
np.digitize(x, bins) - Assign values to bins (returns 1-based indices)
np.clip(array, min_val, max_val) - Constrain values to range
np.isfinite(array) - Boolean mask for finite values
np.arange(start, stop, step) - Create regular coordinate arrays

# Pandas DataFrame Operations
pd.DataFrame(data) - Create DataFrame from list of dicts
df.to_csv(filename, index=False, float_format='%.6f') - Export with precision control

# Memory Management
array.flatten() - Convert to 1D array (creates copy)
array[mask] - Boolean indexing for filtering
