---
name: cmb_power_spectrum
description: "# CMB Angular Power Spectrum Analysis

Create a command-line tool that computes the angular power spectrum from Cosmic Microwave Background (CMB) temperature maps using spherical harmonic analysis.

T"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: astronomy
---

# Cmb Power Spectrum

## Overview
This skill creates a command-line tool for computing angular power spectra from Cosmic Microwave Background (CMB) temperature maps. It uses HEALPix format maps and performs spherical harmonic analysis to extract the power spectrum C_l, which is fundamental for CMB cosmological analysis.

## When to Use
- Analyzing synthetic or real CMB temperature maps in HEALPix format
- Computing angular power spectra for cosmological parameter estimation
- Validating CMB simulations against theoretical predictions
- Educational purposes for understanding CMB data analysis pipelines

## Inputs
- **input_file**: NumPy array file (.npy) containing CMB temperature map in HEALPix format
- **--lmax**: Maximum multipole for analysis (optional, auto-detected from map resolution)
- **--output-json**: Output JSON file for numerical results (default: power_spectrum.json)
- **--output-plot**: Output plot file (default: power_spectrum.png)

## Workflow
1. Load CMB temperature map using scripts/main.py load_cmb_map() function
2. Validate HEALPix format and detect NSIDE parameter
3. Remove monopole and dipole components (standard CMB preprocessing)
4. Compute spherical harmonic coefficients using healpy.map2alm()
5. Convert to angular power spectrum using healpy.alm2cl()
6. Extract multipoles l≥2 and compute statistics
7. Save results to JSON and create diagnostic plot
8. Follow detailed steps in references/workflow.md

## Error Handling
The tool includes comprehensive error handling for common issues:
- File loading errors with informative messages
- Invalid HEALPix format detection and validation
- Array dimension mismatches during spherical harmonic transforms
- Zero or invalid power spectrum values with diagnostic logging
- Plotting failures due to data type incompatibilities

## Common Pitfalls
- Using inefficient manual spherical harmonic computation instead of optimized healpy
- Incorrect array indexing when extracting power spectrum from alm coefficients
- Data type mismatches between numpy arrays causing plotting errors
- Not handling monopole/dipole removal properly for cosmological analysis
- See references/pitfalls.md for detailed error scenarios and fixes

## Output Format
JSON file contains:
- multipoles: Array of l values (integers)
- power_spectrum: Array of C_l values (float64)
- statistics: Dictionary with total_power, peak_multipole, rms_temperature, zero_fraction
- units: "microkelvin^2"

PNG plot shows l(l+1)C_l/(2π) vs multipole l in standard CMB format.
