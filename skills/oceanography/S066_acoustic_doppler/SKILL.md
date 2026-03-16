---
name: adcp_velocity_qc
description: "ADCP Velocity Profile Quality Control and Analysis - Create a CLI script that processes Acoustic Doppler Current Profiler (ADCP) velocity data to identify and remove bad measurements, then compute oceanographic statistics with proper error handling for real-world datasets."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: oceanography
---

# ADCP Velocity Profile Quality Control and Analysis

## Overview
This skill provides comprehensive quality control (QC) processing for Acoustic Doppler Current Profiler (ADCP) velocity data. It implements multiple oceanographic QC algorithms including phase-space spike detection, beam correlation filtering, echo intensity analysis, and vertical shear validation. The tool handles real-world ADCP datasets with CSV format, headers, text-based NaN values, and data gaps.

## When to Use
- Processing raw ADCP velocity measurements from oceanographic cruises
- Identifying and removing erroneous velocity spikes and low-quality measurements
- Computing depth-averaged currents and oceanographic statistics
- Generating quality control reports and velocity profile visualizations
- Preparing ADCP data for further oceanographic analysis

## Inputs
- U, V, W velocity component CSV files with headers
- Beam correlation data (1D or 2D arrays)
- Echo intensity measurements
- Depth bin information
- Quality control thresholds (correlation, spike detection)

## Workflow
1. Load ADCP data using scripts/main.py with CSV parsing and NaN handling
2. Apply phase-space spike detection algorithm to identify velocity outliers
3. Filter data based on beam correlation thresholds
4. Analyze echo intensity to flag weak acoustic returns
5. Validate vertical shear against oceanographic limits
6. Combine all QC flags and apply final data filtering
7. Compute oceanographic statistics with proper JSON serialization
8. Generate velocity profile plots and quality control visualizations
9. Reference references/pitfalls.md for common data loading and processing issues

## Error Handling
The system must handle various error conditions robustly. Data loading errors are handled through pandas CSV parsing with multiple NaN representations. Boolean operation errors with NaN arrays are resolved using explicit masking. JSON serialization errors from NaN values are fixed by converting to null values. The error handling ensures processing continues even with sparse or gapped datasets.

## Common Pitfalls
- Using np.loadtxt() instead of pandas for CSV files with headers and text NaN values
- Boolean array operations failing when NaN values are present in comparisons
- JSON serialization errors when statistical results contain NaN values
- Insufficient data validation before applying median filters and gradient calculations

## Output Format
- JSON file with oceanographic statistics (depth-averaged velocities, standard deviations, data quality percentage)
- PNG visualization showing original vs QC'd velocity profiles, correlation values, and quality flags
- Logging output with processing status and data quality metrics
- All NaN values properly converted to JSON null for valid output format
