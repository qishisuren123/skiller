# scipy.interpolate.interp1d parameters
interp1d(x, y, kind='linear', bounds_error=False, fill_value=(first_val, last_val))
# kind: 'linear', 'nearest', 'cubic'
# bounds_error=False: allows extrapolation
# fill_value: tuple for (below, above) bounds values

# numpy array operations
np.clip(array, min_val, max_val)  # Clip values to range
np.arange(start, stop, step)      # Generate uniform array
np.full(shape, fill_value, dtype) # Create filled array

# pandas DataFrame operations
df.sort_values('column').reset_index(drop=True)  # Sort and reset index
df.apply(func, axis=1)  # Row-wise application (avoid for complex boolean logic)
df['col'].min(), df['col'].max()  # Get column statistics
