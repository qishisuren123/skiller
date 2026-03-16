---
name: uv_spectroscopy
description: "Write a Python CLI script to detect and analyze peaks in UV-Vis absorption spectroscopy data.

Input: A CSV file with columns: wavelength (nm), absorbance. May contain multiple samples as additional columns."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: chemistry
---

# UV Spectroscopy Peak Analysis

## Overview
This skill creates a Python CLI tool for analyzing UV-Vis absorption spectroscopy data. It detects peaks in absorption spectra, calculates peak properties (wavelength, height, FWHM, area), and outputs results as JSON. The tool handles multiple samples, provides comprehensive logging, and includes robust error handling for noisy data.

## When to Use
- Analyzing UV-Vis absorption spectra from spectrophotometers
- Identifying characteristic absorption peaks in chemical samples
- Calculating peak properties for quantitative analysis
- Processing multiple samples in batch
- Quality control of spectroscopic measurements

## Inputs
- CSV file with wavelength column (nm) and one or more absorbance columns
- Peak detection parameters (minimum height, minimum distance)
- Verbosity level for logging output

## Workflow
1. Run `scripts/main.py` with input CSV file and parameters
2. Script loads and validates spectroscopic data with type conversion
3. For each sample, detect peaks using scipy.signal.find_peaks
4. Calculate FWHM using peak_widths with zero-width error handling
5. Compute baseline-corrected peak areas using trapezoidal integration
6. Output results to JSON file with peak properties and sample summaries
7. Review `references/pitfalls.md` for common error patterns and solutions

## Error Handling
The script includes comprehensive error handling for common spectroscopy data issues:
- Handles string data conversion with pd.to_numeric() and error coercion
- Manages zero-width peaks that cause peak_widths() failures in noisy data
- Validates array dimensions and data types before scipy operations
- Provides detailed logging to track processing steps and identify issues

## Common Pitfalls
- Peak area calculations giving negative values due to missing baseline correction
- Array dimension errors when passing incorrect formats to scipy functions
- Data type errors from CSV files with mixed string/numeric content
- Zero-width peak crashes in very noisy spectroscopic data

## Output Format
JSON file containing for each sample:
- peaks: Array of peak objects with wavelength, height, fwhm, area
- dominant_peak: Highest peak with all properties
- n_peaks: Total number of detected peaks
