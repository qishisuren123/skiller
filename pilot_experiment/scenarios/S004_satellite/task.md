Write a Python CLI script to preprocess satellite brightness temperature data stored in NetCDF format.

Input: A NetCDF file with variables:
- brightness_temp: (n_scanlines, n_pixels) float32 array
- latitude: (n_scanlines, n_pixels) float32
- longitude: (n_scanlines, n_pixels) float32
- quality_flag: (n_scanlines, n_pixels) int8 (0=good, 1=suspect, 2=bad)

Requirements:
1. Use argparse: --input NetCDF path, --output CSV path, --resolution (default 0.25 degrees)
2. Mask pixels with quality_flag >= 2 (bad data)
3. Regrid the swath data onto a regular lat/lon grid at the specified resolution
4. For each grid cell, compute mean brightness temperature from valid pixels
5. Output CSV with columns: lat, lon, mean_bt, n_valid_pixels
6. Print summary: total pixels, valid pixels, grid dimensions
