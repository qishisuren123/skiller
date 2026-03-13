# scipy.interpolate.interp1d key parameters:
# - kind='linear': Linear interpolation between points
# - bounds_error=False: Don't raise error for out-of-bounds values
# - fill_value=np.nan: Fill out-of-bounds with NaN instead of extrapolating

# numpy.gradient for oceanographic gradients:
# np.gradient(temperature, depth) - computes dT/dz
# Returns negative values when temperature decreases with depth (normal)
# Use np.argmin() to find steepest negative gradient (thermocline)

# pandas DataFrame operations:
# df.groupby('station_id') - group by station
# df.sort_values('depth_m') - sort by depth
# df['column'].min()/max() - get range

# JSON handling for numpy types:
# Use custom JSONEncoder class to handle np.nan, np.int64, np.float64
# Convert np.nan to None (JSON null)
