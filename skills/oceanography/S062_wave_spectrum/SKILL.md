---
name: wave_spectrum
description: "# Ocean Wave Frequency Spectrum Analysis

Create a CLI script that processes synthetic ocean buoy data to compute and analyze wave frequency spectra. Ocean buoys measure sea surface elevation over time, and spectral analysis reveals the energy distribution across different wave frequencies."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: oceanography
---

# Wave Spectrum

## Overview
This skill provides a complete toolkit for analyzing ocean wave frequency spectra from buoy data. It automatically detects column formats, performs quality control, computes power spectral density using Welch's method, and calculates standard oceanographic parameters like significant wave height and peak frequency. The tool handles common data format variations and provides robust error handling for spectral calculations.

## When to Use
- Analyzing time series data from ocean buoys or wave gauges
- Computing wave statistics from sea surface elevation measurements
- Quality control and validation of oceanographic datasets
- Research requiring standardized wave parameter calculations
- Automated processing of multiple buoy datasets

## Inputs
- CSV file with time series data containing timestamp and elevation columns
- Flexible column name detection (supports 'time'/'timestamp', 'elevation'/'sea_level', etc.)
- Data should be regularly sampled with reasonable temporal resolution
- Elevation values expected in meters

## Workflow
1. Execute scripts/main.py with input CSV file path
2. Script auto-detects time and elevation column names using references/workflow.md patterns
3. Performs quality control checks for unrealistic values and data gaps
4. Preprocesses data with detrending and sampling frequency calculation
5. Computes power spectral density using Welch's method with Hanning windows
6. Calculates wave parameters from spectrum integration over wave frequency band
7. Generates publication-quality visualization and saves results in JSON/CSV formats

## Error Handling
The system includes comprehensive error handling for common issues. Column detection errors are handled by trying multiple naming patterns and providing clear error messages. Spectral calculation errors from unrealistic energy values are caught and logged with diagnostic information. Data quality issues like excessive missing values or unrealistic elevation ranges trigger appropriate warnings and error responses.

## Common Pitfalls
- Assuming fixed column names instead of implementing flexible detection
- Incorrect spectral integration leading to physically impossible energy calculations
- Not validating that wave band energy is less than total spectrum energy
- Insufficient quality control for unrealistic elevation values
- Poor handling of irregular sampling or data gaps

## Output Format
- JSON summary file with wave parameters (significant wave height, peak frequency, etc.)
- CSV file with full spectrum data including frequencies and power spectral density
- PNG visualization showing log-log spectrum plot with wave frequency band highlighted
- All outputs saved to specified directory with standardized naming
