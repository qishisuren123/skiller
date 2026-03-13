# Example 1: Basic quality control and masking
import numpy as np
from netCDF4 import Dataset

with Dataset('satellite_data.nc', 'r') as nc:
    bt = nc.variables['brightness_temp'][:]
    qf = nc.variables['quality_flag'][:]
    
# Apply quality mask
good_data_mask = (qf < 2) & np.isfinite(bt)
clean_bt = bt[good_data_mask]
print(f"Filtered {bt.size - clean_bt.size} bad pixels")

# Example 2: Spatial binning with statistics
lat_bins = np.arange(-90, 91, 0.25)
lon_bins = np.arange(-180, 181, 0.25)

# Assign pixels to grid cells
lat_indices = np.digitize(valid_lats, lat_bins) - 1
lon_indices = np.digitize(valid_lons, lon_bins) - 1

# Aggregate statistics per cell
grid_results = []
for i in range(len(lat_bins)-1):
    for j in range(len(lon_bins)-1):
        cell_mask = (lat_indices == i) & (lon_indices == j)
        if np.sum(cell_mask) > 0:  # Check if cell has data
            mean_val = np.mean(brightness_temps[cell_mask])
            grid_results.append({
                'lat': (lat_bins[i] + lat_bins[i+1]) / 2,
                'lon': (lon_bins[j] + lon_bins[j+1]) / 2,
                'mean_bt': mean_val,
                'n_pixels': np.sum(cell_mask)
            })
