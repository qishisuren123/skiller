# Satellite Brightness Temperature Data Processing

## Overview
This skill helps create efficient Python CLI scripts for processing satellite brightness temperature data from NetCDF files, including gridding, quality filtering, outlier removal, and handling longitude wraparound issues.

## Workflow
1. **Load NetCDF data** using xarray and extract brightness temperature, coordinates, and quality flags
2. **Apply quality filtering** by masking pixels with poor quality flags
3. **Handle longitude wraparound** by detecting dateline crossings and converting to 0-360° system
4. **Remove outliers** using IQR method (1.5×IQR beyond Q1/Q3)
5. **Create aligned grid** by aligning boundaries to resolution using floor/ceil operations
6. **Convert coordinates to grid indices** using vectorized operations
7. **Group pixels by grid cell** using defaultdict for efficient aggregation
8. **Apply minimum pixel filtering** to ensure statistical significance
9. **Calculate grid cell statistics** and output to CSV format

## Common Pitfalls
- **Boolean array ambiguity**: Separate complex boolean conditions into individual variables before combining with `&` operator
- **Performance bottlenecks**: Avoid nested loops over large grids; use vectorized operations and dictionary grouping instead
- **Grid coordinate errors**: Calculate grid cell centers correctly by adding `resolution/2` to aligned grid edges
- **Boundary issues**: Use actual data bounds from valid pixels, not full array bounds
- **Longitude wraparound**: Detect when longitude range > 180° and convert to consistent coordinate system
- **Statistical reliability**: Filter grid cells with too few pixels for meaningful statistics

## Error Handling
- Check for longitude wraparound by comparing longitude range to 180°
- Validate grid indices are within bounds before processing
- Handle empty grid cells gracefully with defaultdict
- Provide comprehensive summary statistics for validation
- Add bounds checking for coordinate conversion operations

## Quick Reference
