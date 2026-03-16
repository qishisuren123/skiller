---
name: weather_fronts
description: "# Weather Front Detection from Temperature Gradient Analysis

Create a CLI script that detects weather fronts by analyzing temperature gradients in atmospheric data. Weather fronts are boundaries between air masses with different temperatures, identified as ridge lines in the gradient field where temperature changes are locally maximal."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: atmospheric
---

# Weather Front Detection

## Overview
This skill implements weather front detection from atmospheric temperature data using gradient ridge analysis. Weather fronts are boundaries between air masses with different temperatures, appearing as narrow zones of high temperature gradients. The script identifies these fronts by detecting ridge lines where gradients are locally maximal perpendicular to the gradient direction.

## When to Use
- Analyzing atmospheric temperature fields from weather models or observations
- Detecting frontal boundaries in meteorological data
- Processing gridded temperature data stored in HDF5 format
- Creating visualizations of weather fronts overlaid on temperature fields
- Extracting quantitative properties of frontal systems

## Inputs
- HDF5 file containing 2D temperature grid, latitude/longitude arrays, and grid spacing
- Gradient threshold for front detection (°C/km)
- Minimum front length in grid points
- Gaussian smoothing parameter for noise reduction

## Workflow
1. Load temperature data from HDF5 file using scripts/main.py
2. Apply Gaussian smoothing to reduce noise
3. Calculate temperature gradients using optimized scipy operations
4. Detect gradient ridges using directional second derivatives
5. Filter connected components by minimum length
6. Extract front properties and coordinates
7. Save results as JSON and create visualization
8. Follow detailed steps in references/workflow.md

## Error Handling
The script includes comprehensive error handling for common issues. File loading errors are handled with informative messages. Array indexing errors during coordinate extraction are prevented by proper dimension checking. Division by zero in gradient calculations is handled using safe division operations. The ridge detection handles edge cases where no fronts are detected.

## Common Pitfalls
- Coordinate indexing mismatches between 2D grids and 1D coordinate arrays
- Incorrect gradient calculation syntax causing axis errors
- Broad gradient regions instead of thin ridge lines without proper ridge detection
- Performance bottlenecks with large datasets requiring optimization
- See references/pitfalls.md for detailed error cases and solutions

## Output Format
JSON file containing front properties (ID, coordinates, gradient strength, length) and PNG visualization showing temperature field with detected fronts as thin boundary lines.
