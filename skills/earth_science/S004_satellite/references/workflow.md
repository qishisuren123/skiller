# Satellite Data Processing Workflow

1. **Data Loading**
   - Open NetCDF file using xarray
   - Extract brightness_temp, latitude, longitude, quality_flag arrays
   - Close dataset to free memory

2. **Quality Filtering**
   - Apply mask where quality_flag >= 2
   - Set invalid pixels to NaN in brightness temperature array

3. **Coordinate Validation**
   - Flatten all arrays for processing
   - Remove pixels with NaN coordinates or brightness temperatures
   - Check for empty dataset after filtering

4. **Dateline Handling**
   - Detect if longitude range > 180° (indicates dateline crossing)
   - Convert negative longitudes to 0-360° range if needed
   - Maintain proper grid bounds

5. **Grid Definition**
   - Calculate grid bounds using floor/ceil operations
   - Create regular lat/lon arrays with specified resolution
   - Convert back to -180/180° range for output if dateline crossed

6. **Vectorized Regridding**
   - Convert coordinates to grid indices
   - Use numpy.bincount for efficient aggregation
   - Calculate mean brightness temperatures per grid cell

7. **Output Generation**
   - Create CSV with lat, lon, mean_bt, n_valid_pixels columns
   - Handle empty datasets with proper headers
   - Generate processing summary statistics
