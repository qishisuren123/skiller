# Hardness Mapping from Indentation Data

Create a CLI script that processes hardness indentation measurements and generates 2D hardness maps using advanced interpolation techniques.

Your script should accept hardness indentation data (position coordinates and hardness values) and produce high-resolution 2D hardness maps. The data represents measurements taken at irregular positions across a material surface using techniques like nanoindentation or microhardness testing.

## Requirements

1. **Data Processing**: Parse input hardness data containing X, Y coordinates (in micrometers) and hardness values (in GPa). Handle missing or invalid measurements by filtering them out and report the number of valid data points processed.

2. **Multi-method Interpolation**: Implement at least three different interpolation methods:
   - Radial Basis Function (RBF) interpolation
   - Inverse Distance Weighting (IDW) 
   - Kriging-based interpolation using scipy's gaussian process capabilities
   
3. **Adaptive Grid Generation**: Create an output grid with resolution automatically determined by data density. Areas with sparse data should use coarser resolution, while dense regions should have finer resolution. The grid should cover the full extent of input data with 10% padding.

4. **Uncertainty Quantification**: Calculate and output interpolation uncertainty maps for each method, representing the confidence in hardness predictions at each grid point based on local data density and interpolation method characteristics.

5. **Statistical Analysis**: Generate summary statistics including hardness distribution histograms, spatial autocorrelation analysis, and method comparison metrics (RMSE, correlation coefficients between methods).

6. **Output Generation**: Save results as HDF5 files containing interpolated hardness maps, uncertainty maps, adaptive grids, and metadata. Also generate PNG visualization plots showing hardness maps with contour lines and measurement point overlays.

Use argparse for command-line interface with options for input data, output directory, interpolation parameters, and visualization settings.
