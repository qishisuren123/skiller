---
name: grain_size_analysis
description: "# Grain Size Distribution Analysis

Create a CLI script that analyzes grain size measurements from materials science image analysis and computes statistical distributions including percentiles, uniformity coefficients, and specific surface area calculations.

Your script should accept grain diameter measurements and calculate comprehensive materials science statistics."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: materials
---

# Grain Size Distribution Analysis

## Overview

This skill provides a comprehensive CLI tool for analyzing grain size distributions from microscopy data in materials science applications. The tool processes diameter measurements to calculate standard statistical metrics, distribution percentiles (D10, D50, D90), uniformity coefficients, size classifications, and specific surface area calculations. It generates both JSON output for data analysis and histogram visualizations.

## When to Use

- Analyzing grain size distributions from SEM/optical microscopy
- Computing materials science statistical parameters (D10, D50, D90 percentiles)
- Calculating uniformity and curvature coefficients for particle characterization
- Determining specific surface area from grain size and density data
- Generating publication-ready histograms of grain size distributions
- Quality control analysis of powder materials or ceramic microstructures

## Inputs

- **diameters**: Comma-separated list of grain diameter measurements in micrometers
- **density** (optional): Material density in g/cm³ for specific surface area calculation
- **output** (optional): Output JSON file path (default: grain_analysis.json)

## Workflow

1. Execute `scripts/main.py` with diameter measurements as command line arguments
2. The script parses and validates input data, removing invalid values (zeros, NaN, negatives)
3. Calculate basic statistics (mean, median, standard deviation, min/max)
4. Compute distribution metrics including D10, D30, D50, D60, D90 percentiles
5. Calculate uniformity coefficient (Cu = D60/D10) and curvature coefficient (Cc = D30²/(D60×D10))
6. Classify grains into size categories (fine <50μm, medium 50-200μm, coarse >200μm)
7. Generate histogram visualization using matplotlib with proper binning
8. Calculate specific surface area if density provided using SSA = 6/(ρ × d_mean)
9. Export comprehensive results to JSON format
10. Reference `references/workflow.md` for detailed step-by-step procedures

## Error Handling

The script implements robust error handling for common data quality issues. It automatically detects and removes invalid measurements including NaN values, zero or negative diameters, and infinite values. Division by zero errors in coefficient calculations are handled by setting values to null rather than infinity to maintain JSON compatibility. The error handling system logs all data cleaning operations and provides detailed feedback on removed measurements, ensuring users understand data quality impacts on their analysis.

## Common Pitfalls

- **Argparse attribute errors**: Using multiple argument names without explicit dest parameter
- **JSON serialization failures**: Setting coefficients to float('inf') instead of null for invalid calculations  
- **Histogram rendering issues**: Data type incompatibilities between numpy arrays and matplotlib
- **Division by zero**: Not validating D10 values before calculating uniformity coefficients
- **Data scope errors**: Using original data instead of cleaned data for visualizations

## Output Format
