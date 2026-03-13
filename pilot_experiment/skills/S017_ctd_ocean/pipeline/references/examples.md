# Example interpolation with bounds checking:
interp_func = interp1d(station_data['depth_m'], station_data['temperature_C'], 
                      kind='linear', bounds_error=False, fill_value=np.nan)
temp_interp = interp_func(standard_depth_grid)

# Example thermocline calculation:
dt_dz = np.gradient(temperature, depth)
thermocline_idx = np.argmin(dt_dz)  # Most negative gradient
thermocline_depth = depth[thermocline_idx]

# Example mixed layer depth:
surface_temp = temperature[0]
temp_diff = np.abs(temperature - surface_temp)
mixed_layer_idx = np.where(temp_diff > 0.5)[0]
mixed_layer_depth = depth[mixed_layer_idx[0]] if len(mixed_layer_idx) > 0 else depth[-1]

# Example standardized depth grid:
global_min = df['depth_m'].min()
global_max = df['depth_m'].max()
grid_start = np.floor(global_min / resolution) * resolution
grid_end = np.ceil(global_max / resolution) * resolution
depth_grid = np.arange(grid_start, grid_end + resolution, resolution)

# Example sigma-t calculation:
sigma_t = (-0.093 + 0.808*salinity - 0.0016*salinity**2 + 
           (-0.0069 + 0.0025*salinity)*temperature - 0.0001*temperature**2)
