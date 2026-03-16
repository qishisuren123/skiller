---
name: hardness_mapping
description: "# Hardness Mapping from Indentation Data

Create a CLI script that processes hardness indentation measurements and generates 2D hardness maps using advanced interpolation techniques.

Your script should handle multiple file formats, perform RBF/IDW/Kriging interpolation, calculate spatial statistics, and output HDF5 files with visualizations."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: materials
---

# Hardness Mapping

## Overview
This skill processes nanoindentation hardness measurements to create 2D spatial maps using advanced interpolation methods. It handles data loading, cleaning, multiple interpolation algorithms (RBF, IDW, Kriging), statistical analysis, and generates comprehensive outputs including HDF5 files and publication-ready visualizations.

## When to Use
- Processing nanoindentation or microindentation hardness data
- Creating spatial hardness maps from scattered measurement points
- Comparing different interpolation methods for materials characterization
- Analyzing spatial patterns and autocorrelation in mechanical properties
- Generating uncertainty maps for interpolated data

## Inputs
- Data files: CSV, Excel, or tab-delimited text files
- Required columns: X coordinates, Y coordinates, Hardness values (flexible naming)
- Optional parameters: grid resolution, padding factor, interpolation settings

## Workflow
1. Execute `python scripts/main.py input_data.txt -o output_dir --resolution 50`
2. Script loads and validates data, handling multiple file formats automatically
3. Creates adaptive interpolation grid with specified resolution and padding
4. Performs three interpolation methods: RBF, IDW, and optimized Kriging
5. Calculates comprehensive statistics and spatial autocorrelation analysis
6. Saves results to HDF5 format and generates visualization plots
7. Review `references/pitfalls.md` for common issues and solutions

## Error Handling
The system includes robust error handling for data loading issues, file format detection, column identification, and large dataset optimization. When Kriging encounters performance issues with large datasets, the system automatically applies subsampling and chunked processing to handle memory constraints efficiently.

## Common Pitfalls
- File path handling errors when using Path objects with pandas functions
- Kriging performance degradation with large datasets (>500 points)
- Column detection failures with non-standard naming conventions
- Memory issues during interpolation grid processing

## Output Format
- HDF5 file containing original data, grids, interpolation results, and statistics
- PNG visualizations: hardness distribution histogram, spatial autocorrelation plot
- Individual hardness and uncertainty maps for each interpolation method
- Progress logging and performance timing information
