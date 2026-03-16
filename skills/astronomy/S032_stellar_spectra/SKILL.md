---
name: stellar_spectra
description: "# Stellar Spectra Classification and Normalization

Create a command-line tool that processes synthetic stellar spectra data to perform normalization and spectral type classification. Your script shou"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: astronomy
---

# Stellar Spectra Classification and Normalization

## Overview
This skill provides a comprehensive tool for processing stellar spectra, including continuum normalization, equivalent width measurements, and automated spectral type classification. The tool handles synthetic spectra generation for testing and includes robust error handling for noisy data. It extracts key spectral features like Balmer line ratios, Ca H&K strengths, and continuum slopes to classify stars into O, B, A, F, G, K, M spectral types with confidence scores.

## When to Use
- Processing stellar spectra for automated classification
- Normalizing spectra to remove instrumental effects
- Extracting equivalent widths of key absorption lines
- Testing classification algorithms with synthetic data
- Quality assessment of spectroscopic observations
- Batch processing of large spectral datasets

## Inputs
- Wavelength range (default: 3500-7000 Angstroms)
- Number of synthetic spectra to generate
- Signal-to-noise ratio for synthetic data
- Output directory for results
- Optional: Real spectral data files (HDF5 format)

## Workflow
1. Execute `scripts/main.py` with desired parameters
2. Generate synthetic stellar spectra with realistic absorption lines
3. Fit polynomial continuum using iterative sigma clipping
4. Normalize spectra by dividing by fitted continuum
5. Calculate equivalent widths for key spectral lines (H-alpha, H-beta, Ca H&K, Mg I)
6. Extract additional features (continuum slope, line depths, SNR)
7. Apply classification algorithm using weighted feature comparison
8. Generate confidence scores and quality flags
9. Save results to HDF5 files and JSON summary
10. Reference `references/workflow.md` for detailed processing steps

## Error Handling
The tool includes comprehensive error handling for numerical instabilities. When polynomial fitting fails due to SVD convergence issues with noisy data, the system automatically scales wavelength values and falls back to lower-order polynomials. If all polynomial fits fail, it uses median continuum as a fallback. The error handling also manages division by zero in normalization, validates equivalent width calculations, and handles NaN/infinity values gracefully.

## Common Pitfalls
- SVD convergence failures with high-noise spectra (SNR < 5)
- Numerical instability from large wavelength values in polynomial fitting
- Division by zero when continuum approaches zero
- Insufficient data points after sigma clipping
- Invalid equivalent width calculations with sparse wavelength coverage
- See `references/pitfalls.md` for complete error scenarios and solutions

## Output Format
- HDF5 files containing normalized spectra, original flux, and continuum fits
- JSON file with classification results, equivalent widths, and confidence scores
- Each spectrum includes spectral type, probability distribution, and quality flags
- Feature measurements with uncertainty estimates
- Processing logs with quality assessment information
