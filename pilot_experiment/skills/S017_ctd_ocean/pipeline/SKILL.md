# CTD Oceanographic Data Processing with Python CLI

## Overview
This skill helps create a robust Python CLI script for processing CTD (Conductivity, Temperature, Depth) oceanographic profile data. It handles interpolation to standardized depth grids, computes derived parameters like potential density (sigma-t), and identifies key oceanographic features like thermocline and mixed layer depths.

## Workflow
1. **Setup argument parsing** with input file, output directory, and depth resolution parameters
2. **Read and validate input data** from CSV format
3. **Create standardized depth grid** across all stations for consistent comparison
4. **Process each station individually**:
   - Sort data by depth
   - Interpolate temperature, salinity, and dissolved oxygen to standard grid
   - Compute derived parameters (sigma-t)
   - Calculate thermocline depth (maximum negative temperature gradient)
   - Calculate mixed layer depth (first depth where temperature differs >0.5°C from surface)
5. **Handle edge cases** (insufficient data, constant profiles)
6. **Export results** as CSV (profiles) and JSON (station summaries)

## Common Pitfalls
- **Interpolation range errors**: Don't start depth grid at 0 if CTD data starts deeper - use actual minimum depth from data
- **Thermocline calculation error**: Use `np.argmin()` for steepest negative gradient, not `np.argmax()` 
- **Mixed layer depth inconsistency**: Calculate using only actual measurement depths, not extrapolated shallow depths
- **JSON serialization of NaN**: Use custom encoder to convert numpy NaN to JSON null
- **Inconsistent station comparison**: Standardize depth grids across all stations, fill missing depths with NaN

## Error Handling
- Check for minimum data points (need ≥3 for thermocline, ≥2 for mixed layer)
- Validate temperature range (>0.1°C variation for thermocline, >0.5°C for mixed layer)
- Use `bounds_error=False` and `fill_value=np.nan` for interpolation safety
- Filter NaN values when computing statistics
- Provide informative warnings for stations with insufficient data

## Quick Reference
