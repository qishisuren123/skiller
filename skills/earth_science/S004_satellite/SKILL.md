---
name: satellite_brightness_temperature_preprocessing
description: "Write a Python CLI script to preprocess satellite brightness temperature data stored in NetCDF format.

Input: A NetCDF file with variables:
- brightness_temp: (n_scanlines, n_pixels) float32 array
- latitude: (n_scanlines, n_pixels) float32 array  
- longitude: (n_scanlines, n_pixels) float32 array
- quality_flag: (n_scanlines, n_pixels) int array

Output: CSV file with regridded data containing lat, lon, mean_bt, n_valid_pixels columns."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: earth_science
---

# Satellite Brightness Temperature Preprocessing

## Overview
This skill provides a complete solution for preprocessing satellite brightness temperature data from swath format to regular lat/lon grids. It handles quality filtering, efficient regridding using vectorized operations, and special cases like dateline crossing and empty datasets.

## When to Use
- Processing microwave satellite data (AMSR, SSMIS, etc.)
- Converting swath data to regular grids for analysis
- Batch processing of satellite files with quality control
- Handling global datasets that may cross the dateline

## Inputs
- NetCDF file with brightness_temp, latitude, longitude, quality_flag variables
- Grid resolution in degrees (default 0.25°)
- Output CSV file path

## Workflow
1. Execute `python scripts/main.py --input data.nc --output results.csv --resolution 0.25`
2. Script loads NetCDF data and applies quality filtering (quality_flag >= 2 marked as invalid)
3. Detects dateline crossing and adjusts longitude coordinates if needed
4. Uses vectorized regridding with numpy.bincount for efficient aggregation
5. Outputs CSV with lat, lon, mean_bt, n_valid_pixels columns
6. Refer to `references/workflow.md` for detailed processing steps

## Error Handling
The script includes robust error handling for common issues:
- Empty datasets after quality filtering: Creates empty CSV with proper headers
- Dateline crossing: Automatically detects and handles longitude wraparound
- Invalid coordinates: Filters NaN values before processing
- Memory efficiency: Uses vectorized operations to handle large files (2GB+)

## Common Pitfalls
- Initial nested loop approach was extremely slow for large datasets
- Incorrect aggregation logic caused unrealistic brightness temperature values
- Dateline crossing created artificially wide grids spanning 360° longitude
- See `references/pitfalls.md` for detailed error cases and solutions

## Output Format
CSV file with columns:
- lat: Grid cell center latitude
- lon: Grid cell center longitude  
- mean_bt: Mean brightness temperature (K)
- n_valid_pixels: Number of valid pixels in cell
