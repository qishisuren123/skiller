# UV-Vis Spectroscopy Peak Detection and Analysis

## Overview
This skill enables detection and quantitative analysis of absorption peaks in UV-Vis spectroscopy data, providing critical parameters like peak position, intensity, width, and area for spectroscopic characterization.

## Workflow
1. Parse command-line arguments for input CSV, output JSON, and detection parameters (min-height, min-distance)
2. Load CSV data with wavelength column and one or more sample absorbance columns
3. For each sample, apply scipy.signal.find_peaks with prominence-based detection using min-height and converted min-distance
4. Calculate peak properties: extract peak heights, compute FWHM using peak widths at half maximum, integrate peak areas using trapezoidal rule
5. Identify dominant peak as the one with maximum absorbance value among detected peaks
6. Structure results as nested dictionary with sample-level peak arrays and metadata
7. Export JSON results and print summary statistics including peak counts and dominant peak wavelength ranges

## Common Pitfalls
- **Wavelength spacing assumption**: Always convert min-distance from nm to data point indices using actual wavelength spacing, don't assume uniform 1nm intervals
- **Insufficient peak prominence**: Low min-height values may detect noise as peaks; start with 0.1 and adjust based on baseline noise levels in your spectra
- **FWHM calculation errors**: scipy's peak_widths returns widths in data point indices - convert back to wavelength units using the wavelength array spacing
- **Integration boundary issues**: For peak area calculation, ensure integration limits don't exceed array bounds when defining peak base regions
- **Missing data handling**: Check for NaN values in absorbance data which can cause find_peaks to fail silently

## Error Handling
- Validate CSV structure and required columns before processing
- Handle samples with no detected peaks by returning empty peak arrays
- Catch and report scipy.signal errors with informative messages about parameter adjustment
- Ensure wavelength data is monotonically increasing for proper peak detection

## Quick Reference
