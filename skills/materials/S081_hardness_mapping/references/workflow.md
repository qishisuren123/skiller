1. Prepare input data file with X, Y coordinates and hardness values in CSV, Excel, or tab-delimited format
2. Run the script: `python scripts/main.py input_data.txt -o output_directory --resolution 50 --verbose`
3. Script automatically detects file format and identifies coordinate/hardness columns using flexible naming
4. Data cleaning removes invalid points (NaN, infinite, negative hardness values)
5. Adaptive grid generation creates interpolation mesh with specified resolution and padding
6. Three interpolation methods execute: RBF (thin plate spline), IDW (power=2), and optimized Kriging
7. Statistical analysis calculates basic statistics, method correlations, and RMSE comparisons
8. Spatial autocorrelation analysis determines correlation vs distance relationships
9. Results save to HDF5 format containing all data, grids, interpolations, and statistics
10. Visualization generation creates hardness distribution histogram, autocorrelation plot, and hardness/uncertainty maps
11. Review output directory for hardness_results.h5 file and PNG visualization plots
12. Check references/pitfalls.md for troubleshooting common issues
