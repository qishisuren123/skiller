# XRD Pattern Analysis with Python CLI

## Overview
This skill helps create a robust Python CLI script for X-ray diffraction (XRD) pattern analysis, including background subtraction, peak detection, Gaussian fitting, and d-spacing calculations. The script handles edge cases like low signal, noisy data, and missing peaks while generating comprehensive output files.

## Workflow
1. **Setup and argument parsing**: Configure CLI arguments for input file, output directory, wavelength, and detection thresholds
2. **Data validation**: Check for required columns, sufficient data points, and valid intensity values
3. **Background subtraction**: Use minimum filter followed by Gaussian smoothing to estimate and remove background
4. **Peak detection**: Apply adaptive thresholds based on signal quality and noise levels
5. **Gaussian fitting**: Fit individual Gaussian curves to each detected peak with robust parameter estimation
6. **D-spacing calculation**: Apply Bragg's law to convert 2θ positions to d-spacings
7. **Pattern reconstruction**: Generate fitted pattern by combining background with fitted Gaussians
8. **Output generation**: Save peaks.csv, fitted_pattern.csv, and summary.json files

## Common Pitfalls
- **Gaussian fitting convergence issues**: Initial parameter estimation is crucial - use half-maximum points to estimate FWHM and peak width for better starting values
- **Baseline handling in fitting**: Don't double-count baseline - fit to background-corrected data and reconstruct by adding peaks to background
- **Fitted intensity scaling problems**: When reconstructing the full pattern, start with the background array and add Gaussian contributions, don't inflate individual peak intensities
- **Fixed thresholds for diverse data**: Implement adaptive thresholds based on signal-to-noise ratio and maximum intensity
- **Window size issues**: Ensure fitting windows and filter sizes scale appropriately with data size and peak characteristics

## Error Handling
- **Low signal data**: Automatically reduce min_height to 30% of maximum signal and adjust prominence thresholds
- **High noise data**: Increase prominence threshold to 3x noise level to avoid false peaks
- **Fitting failures**: Provide fallback to detected peak parameters when Gaussian fitting fails
- **No peaks detected**: Generate empty output files with proper structure and diagnostic messages
- **Data validation**: Check for required columns, minimum data points, and positive intensities
- **Quality checks**: Validate fitted parameters (sigma bounds, position accuracy) before accepting results

## Quick Reference
