---
name: well_log
description: "Write a Python CLI script to resample borehole well log data and classify lithology from crossplot rules.

Input: A CSV file with columns: depth, gamma_ray, resistivity, neutron_porosity, bulk_density"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: earth_science
---

# Well Log

## Overview
This skill processes borehole well log data by resampling measurements to uniform depth intervals and classifying lithology using petrophysical crossplot rules. It handles CSV files containing depth, gamma ray, resistivity, neutron porosity, bulk density, and caliper measurements.

## When to Use
- Processing raw well log data with irregular depth sampling
- Standardizing well log data to uniform depth intervals
- Automated lithology classification from log measurements
- Generating derived petrophysical parameters (porosity, shale volume)
- Quality control and validation of well log interpretations

## Inputs
- CSV file with required columns: depth, gamma_ray, resistivity, neutron_porosity, bulk_density, caliper
- Depth step for resampling (default: 0.5 meters)
- Optional matrix density for porosity calculation (auto-estimated if not provided)

## Workflow
1. Execute `scripts/main.py` with input CSV file and output directory
2. Load and validate well log data from CSV
3. Resample all log curves to uniform depth intervals using linear interpolation
4. Compute derived logs: PHIT (total porosity) and Vsh (shale volume)
5. Apply lithology classification rules based on crossplot analysis
6. Generate output files: resampled logs, lithology classification, and summary statistics
7. Refer to `references/workflow.md` for detailed processing steps

## Error Handling
The script includes comprehensive error handling for common data issues. It will handle missing data points during interpolation and detect insufficient valid data. When bulk density values exceed typical matrix densities, the system automatically estimates appropriate matrix density to prevent negative porosity calculations. NaN values in derived parameters are properly managed using numpy's nanmean functions to ensure valid statistical summaries.

## Common Pitfalls
- Negative porosity values due to incorrect matrix density assumptions
- All samples classified as single lithology due to zero porosity
- NaN values in summary statistics from improper handling of missing data
- Interpolation failures with scipy compatibility issues across versions

## Output Format
- `resampled_log.csv`: Uniformly sampled log data with derived parameters
- `lithology_classification.csv`: Depth and corresponding lithology assignments
- `summary.json`: Statistical summary including depth range, sample count, lithology distribution, and mean petrophysical properties
