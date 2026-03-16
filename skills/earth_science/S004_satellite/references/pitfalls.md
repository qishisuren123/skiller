# Common Pitfalls and Solutions

## Performance Issues with Nested Loops

**Error**: Initial implementation used nested loops for regridding, causing extremely slow processing (>1 hour for 2GB files)

**Root Cause**: O(n²) complexity when searching for pixels within each grid cell using spatial masks

**Fix**: Replaced with vectorized approach using coordinate-to-index conversion and numpy.bincount for O(n) aggregation

## Incorrect Aggregation Logic

**Error**: Brightness temperatures over 400K and unrealistic pixel counts in grid cells

**Root Cause**: Manual loop accumulation had bugs causing double-counting and incorrect summation

**Fix**: Used numpy.bincount with weights parameter for proper aggregation, ensuring each pixel contributes exactly once

## Empty Dataset Crashes

**Error**: ValueError "No valid data found" when all pixels have quality_flag >= 2

**Root Cause**: Script attempted to create grids from empty coordinate arrays

**Fix**: Added early detection of empty datasets, returning empty arrays and creating CSV with headers only

## Dateline Crossing Artifacts

**Error**: Grids spanning full 360° longitude range for polar orbits crossing dateline

**Root Cause**: Longitude jump from 179° to -179° created artificially wide coordinate bounds

**Fix**: Added dateline detection (longitude range > 180°) and coordinate adjustment to 0-360° range during processing
