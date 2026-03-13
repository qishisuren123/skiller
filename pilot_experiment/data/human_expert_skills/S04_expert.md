# Satellite Brightness Temperature Processing — Expert Notes

## What You're Building
Read satellite swath data from NetCDF, mask bad pixels, regrid onto a regular lat/lon grid, output as CSV.

## Key Steps
1. Open NetCDF — use `scipy.io.netcdf_file` or `netCDF4.Dataset`
2. Apply quality mask: keep only `quality_flag < 2`
3. Build a regular grid based on `--resolution` (default 0.25°)
4. Bin swath pixels into grid cells, compute mean BT per cell
5. Output CSV: lat, lon, mean_bt, n_valid_pixels

## Pitfalls from Experience
1. **NetCDF library**: `scipy.io.netcdf_file` is simpler but only supports NetCDF3. If `netCDF4` is available, prefer it. Either works for simple variables
2. **Swath vs gridded**: The input is swath data — lat/lon are 2D arrays, not 1D axes. Don't try to index like `data[lat_idx, lon_idx]`
3. **Binning approach**: Use `np.digitize` or integer floor division: `lat_bin = ((lat - lat_min) / resolution).astype(int)`. Then group by (lat_bin, lon_bin) and average
4. **NaN handling**: After masking bad pixels, use `np.nanmean` for grid cell averages
5. **Edge case**: Some grid cells will have zero valid pixels — skip them in output, don't output NaN rows

## Reference
```python
lat_bins = ((lats - lat_min) / resolution).astype(int)
lon_bins = ((lons - lon_min) / resolution).astype(int)
for (lb, lonb), group in grouped_data:
    mean_bt = np.nanmean(group_bt)
    rows.append({"lat": lat_min + lb * resolution + resolution/2,
                 "lon": lon_min + lonb * resolution + resolution/2,
                 "mean_bt": mean_bt,
                 "n_valid_pixels": len(group_bt)})
```
