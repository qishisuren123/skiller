# CTD Oceanographic Profile Data Processing

## Overview
This skill processes CTD (Conductivity-Temperature-Depth) oceanographic profile data by interpolating measurements to regular depth grids, computing derived oceanographic parameters like potential density and thermocline characteristics, and generating standardized outputs for marine science analysis.

## Workflow
1. Parse command-line arguments for input CSV file, output directory, and depth resolution parameters
2. Load and validate CTD data ensuring required columns (station_id, depth_m, temperature_C, salinity_PSU, dissolved_oxygen_mL_L) are present
3. Group data by station_id and interpolate each profile to a regular depth grid from 0 to maximum depth at specified resolution
4. Calculate potential density (sigma-t) using the simplified UNESCO equation for each interpolated profile
5. Compute oceanographic features: thermocline depth (maximum dT/dz) and mixed layer depth (temperature difference > 0.5°C from surface)
6. Export interpolated profiles to CSV and station summary statistics to JSON format
7. Display processing summary including station count, depth ranges, and mean thermocline depth

## Common Pitfalls
- **Monotonic depth requirement**: CTD data may have non-monotonic depths due to instrument drift. Solution: Sort by depth and remove duplicate depth values before interpolation
- **Sparse data interpolation**: Interpolating over large depth gaps can create unrealistic values. Solution: Only interpolate within the actual depth range of each station, don't extrapolate beyond measured depths
- **Surface temperature reference**: Mixed layer depth calculation requires valid surface temperature. Solution: Use the shallowest measurement as surface reference, not necessarily depth=0
- **Gradient calculation edge effects**: Temperature gradients at profile boundaries can be unstable. Solution: Use numpy.gradient() which handles edges properly, and exclude boundary points from thermocline detection
- **Missing data handling**: CTD profiles often have missing values for some parameters. Solution: Use pandas interpolate() method with limit parameter to avoid over-interpolation

## Error Handling
- Validate input CSV structure and required columns before processing
- Handle stations with insufficient data points (< 3 measurements) by skipping with warning
- Catch interpolation failures for individual stations and continue processing remaining data
- Ensure output directory exists or create it, handle file permission errors gracefully
- Validate depth resolution parameter to prevent memory issues with very fine grids

## Quick Reference
