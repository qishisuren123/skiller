# SKILL: Satellite Brightness Temperature Data Preprocessing

## Overview
This tool preprocesses satellite brightness temperature data from NetCDF swath format into a regular lat/lon grid. It filters bad quality data, regrids using spatial binning, and outputs aggregated statistics in CSV format for further analysis.

## Workflow

1. **Parse command line arguments** - Set up argparse for input/output paths and grid resolution
2. **Load NetCDF data** - Read brightness temperature, coordinates, and quality flags using xarray/netCDF4
3. **Apply quality mask** - Filter out pixels where quality_flag >= 2 (bad data)
4. **Define output grid** - Create regular lat/lon grid based on data bounds and specified resolution
5. **Spatial binning** - Assign each valid pixel to grid cells using coordinate indexing
6. **Aggregate statistics** - Compute mean brightness temperature and count valid pixels per grid cell
7. **Export results** - Write CSV with lat, lon, mean_bt, n_valid_pixels and print summary statistics

## Common Pitfalls & Solutions

1. **Memory issues with large datasets**
   - *Solution*: Process data in chunks or use dask for lazy loading
   - *Code*: `ds = xr.open_dataset(file, chunks={'n_scanlines': 1000})`

2. **Grid cells with no valid data**
   - *Solution*: Check for empty bins and handle NaN values explicitly
   - *Code*: `mask = counts > 0; mean_bt[~mask] = np.nan`

3. **Coordinate bounds extending beyond valid ranges**
   - *Solution*: Clip lat/lon to valid ranges before gridding
   - *Code*: `lat = np.clip(lat, -90, 90); lon = np.clip(lon, -180, 180)`

4. **Integer overflow in grid indexing**
   - *Solution*: Use proper data types and bounds checking
   - *Code*: `lat_idx = np.clip(lat_idx, 0, n_lat-1).astype(int)`

5. **Inconsistent coordinate ordering**
   - *Solution*: Always verify lat/lon array shapes match brightness_temp
   - *Code*: `assert lat.shape == brightness_temp.shape`

## Error Handling Tips

- Validate NetCDF file structure before processing
- Check for empty datasets after quality filtering
- Handle edge cases where grid resolution is larger than data coverage
- Use try/except blocks around file I/O operations
- Verify output directory exists before writing CSV

## Reference Code Snippet

```python
import numpy as np
import xarray as xr
import pandas as pd

def regrid_swath_data(bt, lat, lon, quality, resolution=0.25):
    # Apply quality mask
    valid_mask = quality < 2
    bt_valid = bt[valid_mask]
    lat_valid = lat[valid_mask]
    lon_valid = lon[valid_mask]
    
    # Define output grid
    lat_bins = np.arange(-90, 90 + resolution, resolution)
    lon_bins = np.arange(-180, 180 + resolution, resolution)
    
    # Convert coordinates to grid indices
    lat_idx = ((lat_valid + 90) / resolution).astype(int)
    lon_idx = ((lon_valid + 180) / resolution).astype(int)
    lat_idx = np.clip(lat_idx, 0, len(lat_bins)-2)
    lon_idx = np.clip(lon_idx, 0, len(lon_bins)-2)
    
    # Spatial binning using numpy
    grid_shape = (len(lat_bins)-1, len(lon_bins)-1)
    bt_sum = np.zeros(grid_shape)
    counts = np.zeros(grid_shape, dtype=int)
    
    np.add.at(bt_sum, (lat_idx, lon_idx), bt_valid)
    np.add.at(counts, (lat_idx, lon_idx), 1)
    
    # Compute means
    mean_bt = np.divide(bt_sum, counts, out=np.full_like(bt_sum, np.nan), where=counts>0)
    
    return mean_bt, counts, lat_bins[:-1], lon_bins[:-1]
```