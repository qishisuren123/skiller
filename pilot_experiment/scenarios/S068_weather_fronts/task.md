# Weather Front Detection from Temperature Gradient Analysis

Create a CLI script that detects weather fronts by analyzing temperature gradients in atmospheric data. Weather fronts are boundaries between air masses with different temperatures, and can be identified by analyzing spatial temperature gradients and their temporal changes.

## Requirements

Your script should accept the following arguments:
- `--input-data`: Path to input HDF5 file containing temperature grid data
- `--output-fronts`: Path to output JSON file containing detected front information
- `--output-plot`: Path to output PNG file showing temperature field with detected fronts
- `--gradient-threshold`: Minimum temperature gradient magnitude (°C/km) to consider for front detection (default: 2.0)
- `--min-front-length`: Minimum length (grid points) for a valid front segment (default: 5)
- `--smoothing-sigma`: Gaussian smoothing parameter for temperature field (default: 1.0)

The input HDF5 file contains:
- `temperature`: 2D array of temperature values (°C) on a regular grid
- `lat`: 1D array of latitude coordinates (degrees)
- `lon`: 1D array of longitude coordinates (degrees)
- `grid_spacing`: Scalar value representing grid spacing in kilometers

## Processing Steps

1. **Data Loading**: Read temperature data and coordinate information from the HDF5 file
2. **Smoothing**: Apply Gaussian smoothing to reduce noise in temperature field
3. **Gradient Calculation**: Compute temperature gradients in both x and y directions, accounting for grid spacing
4. **Front Detection**: Identify regions where gradient magnitude exceeds the threshold
5. **Front Segmentation**: Group connected high-gradient pixels into front segments and filter by minimum length
6. **Output Generation**: Save front locations and properties to JSON, and create visualization plot

The output JSON should contain front segments with their coordinates, average gradient strength, and length. The visualization should show the temperature field as a color map with detected fronts overlaid as contour lines.
