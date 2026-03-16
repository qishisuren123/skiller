---
name: sea_surface_temp
description: "# Sea Surface Temperature Anomaly Analysis

Create a CLI script that processes satellite-derived sea surface temperature (SST) data to compute temperature anomalies and generate summary statistics.

Y"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: oceanography
---

# Sea Surface Temperature Anomaly Analysis

## Overview

This skill provides a comprehensive CLI tool for analyzing sea surface temperature (SST) data from satellite observations. The tool computes temperature anomalies relative to climatological baselines and generates detailed statistical summaries. It handles real-world oceanographic data challenges including missing values (NaN), large datasets, uniform fields, and provides configurable logging for debugging and monitoring.

## When to Use

- Processing satellite-derived SST data for climate analysis
- Computing temperature anomalies for oceanographic research
- Analyzing large gridded temperature datasets with missing data
- Generating statistical summaries of ocean temperature patterns
- Quality control and validation of SST datasets
- Batch processing of multiple SST files with consistent analysis

## Inputs

- **SST Data**: 2D numpy arrays (.npy files) containing temperature values
- **Grid Dimensions**: For synthetic data generation (rows, cols)
- **Output Paths**: JSON statistics file and optional CSV anomaly grid
- **Processing Options**: CSV output control, logging configuration

## Workflow

1. Execute `scripts/main.py` with appropriate command-line arguments
2. Load real SST data from .npy files or generate synthetic test data
3. Compute climatological mean using NaN-aware functions
4. Calculate anomalies by subtracting climatology from original data
5. Generate comprehensive statistics including extremes and thresholds
6. Handle edge cases like uniform fields and missing data
7. Save results to JSON format with optional CSV grid output
8. Review `references/pitfalls.md` for common error patterns and solutions

## Error Handling

The tool implements robust error handling for common oceanographic data issues. It can handle and gracefully process datasets with missing values, uniform temperature fields, and invalid file formats. When errors occur during data loading or processing, the system logs detailed error messages and provides fallback behaviors to ensure analysis completion where possible.

## Common Pitfalls

- CSV output becomes extremely slow and large for high-resolution grids
- NaN values in input data cause entire analysis to return NaN results
- Uniform temperature fields cause argmax/argmin functions to fail
- Large datasets require performance optimization and memory management
- Missing proper logging makes debugging data issues difficult

## Output Format

- **JSON Statistics**: Comprehensive metrics including mean, std, extremes, coverage
- **CSV Grid** (optional): Full anomaly field for spatial analysis
- **Console Output**: Summary statistics and processing status
- **Log Files** (optional): Detailed processing information and warnings
