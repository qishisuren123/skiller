---
name: pulsar_timing
description: "# Pulsar Timing Analysis and Dispersion Measure Computation

Create a CLI script that processes pulsar timing observations to compute timing residuals and derive dispersion measure corrections. This tool fits quadratic timing models, optimizes dispersion measures, and provides comprehensive statistical analysis of pulsar timing data across multiple frequency bands."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: astronomy
---

# Pulsar Timing Analysis

## Overview
This skill provides a complete pipeline for pulsar timing analysis, including quadratic timing model fitting, dispersion measure optimization, and residual computation. The tool processes multi-frequency Time of Arrival (TOA) data to extract timing parameters and correct for interstellar dispersion effects.

## When to Use
- Processing pulsar timing observations with TOA data
- Fitting timing models to extract period and period derivative
- Optimizing dispersion measure corrections across frequency bands
- Computing timing residuals for pulsar characterization
- Analyzing multi-frequency pulsar observations

## Inputs
- CSV file with columns: MJD, frequency, TOA, uncertainty
- Optional output file specifications
- Configurable logging levels

## Workflow
1. Load and validate timing data using scripts/main.py data loading functions
2. Remove statistical outliers (>5σ) and handle missing values
3. Fit quadratic timing model to lowest frequency observations
4. Optimize dispersion measure to minimize residual RMS
5. Calculate final timing residuals with dispersion corrections
6. Generate comprehensive statistics by frequency band
7. Export results to JSON and processed CSV files
8. Reference references/pitfalls.md for common error patterns

## Error Handling
The system includes robust error handling for data validation, timing model convergence issues, and optimization failures. When curve fitting fails to converge, the system will error out with detailed logging. If DM optimization doesn't handle convergence properly, it falls back to default values while logging warnings.

## Common Pitfalls
- Shape mismatches between timing data arrays during curve fitting
- Type errors from pandas Series operations in mathematical calculations
- Incorrect nested dictionary structures for frequency band statistics
- Missing explicit type conversions when extracting DataFrame values

## Output Format
- JSON file with timing parameters, dispersion measure, and residual statistics
- CSV file with original data plus residuals and predicted TOAs
- Frequency-specific statistics for multi-band analysis
- Comprehensive logging of analysis steps and parameter uncertainties
