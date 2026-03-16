---
name: tidal_analysis
description: "# Tidal Harmonic Analysis Tool

Create a command-line tool that performs basic harmonic analysis on synthetic tidal height data to identify dominant tidal constituents and their characteristics."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: oceanography
---

# Tidal Analysis

## Overview
This tool generates synthetic tidal height data and performs FFT-based harmonic analysis to identify dominant tidal constituents (M2, S2, O1, K1, N2). It provides both JSON and CSV output formats with visualization capabilities and includes memory management for large datasets.

## When to Use
- Analyzing tidal data for oceanographic research
- Testing harmonic analysis algorithms with known synthetic data
- Educational purposes for understanding tidal constituent analysis
- Validating tidal prediction models

## Inputs
- Duration in days (integer)
- Sampling interval in hours (float)
- Minimum amplitude threshold in meters (float)
- Output file paths for harmonics and plot
- Optional random seed for reproducibility
- Optional CSV output format

## Workflow
1. Run `scripts/main.py` with required parameters
2. Tool estimates memory usage and validates inputs
3. Generates synthetic tidal data with M2, S2, O1 constituents
4. Performs FFT-based harmonic analysis with adaptive frequency resolution
5. Matches identified frequencies to known tidal constituents
6. Outputs results in JSON/CSV format and creates time series plot
7. Refer to `references/workflow.md` for detailed steps

## Error Handling
The tool includes comprehensive error handling for memory issues, invalid parameters, and file I/O problems. Memory estimation prevents crashes by checking available resources before processing. The system will handle frequency resolution warnings for short duration datasets and provide guidance on optimal parameters.

## Common Pitfalls
- Using too short duration (< 3 days) results in poor frequency resolution
- Very fine sampling intervals can cause memory errors
- Random phases make results non-reproducible without setting seed
- FFT amplitude calculation requires proper normalization for accurate results

## Output Format
JSON format contains array of constituents with fields: constituent, period_hours, amplitude_m, phase_degrees. CSV format provides same data in tabular form. PNG plot shows complete time series. All outputs include metadata about analysis parameters and frequency resolution.
