# Satellite Brightness Temperature Data Preprocessing

## Overview
This skill enables preprocessing of satellite brightness temperature data from NetCDF swath format to regular gridded CSV output, including quality control filtering and spatial regridding with statistical aggregation.

## Workflow
1. Parse command line arguments for input NetCDF file, output CSV path, and grid resolution
2. Load NetCDF data arrays (brightness_temp, latitude, longitude, quality_flag) using appropriate libraries
3. Apply quality control mask to filter out pixels with quality_flag >= 2 (bad data)
4. Create regular lat/lon grid bounds based on data extent and specified resolution
5. Assign each valid swath pixel to appropriate grid cell using spatial binning
6. Compute mean brightness temperature and pixel count statistics for each populated grid cell
7. Export results to CSV format and print processing summary statistics

## Common Pitfalls
- **Swath edge effects**: Satellite swath data has irregular boundaries that can create sparse grid cells at edges. Solution: Check for minimum pixel counts per grid cell before including in output.
- **Memory overflow with large datasets**: Loading entire arrays can exceed memory. Solution: Process data in chunks or use memory-mapped arrays for large files.
- **Coordinate system assumptions**: Assuming lat/lon are in specific units or ranges. Solution: Always validate coordinate bounds and handle dateline crossing cases.
- **Invalid data propagation**: NaN or fill values in brightness_temp can corrupt statistics. Solution: Apply np.isfinite() checks in addition to quality flag filtering.
- **Grid cell assignment errors**: Floating point precision issues in binning. Solution: Use np.digitize() or explicit floor operations for robust grid assignment.

## Error Handling
- Validate NetCDF file structure and required variables exist before processing
- Handle coordinate edge cases (dateline crossing, polar regions) with appropriate bounds checking
- Implement memory-efficient processing for large datasets using chunked operations
- Provide informative error messages for invalid grid resolutions or empty output scenarios

## Quick Reference
