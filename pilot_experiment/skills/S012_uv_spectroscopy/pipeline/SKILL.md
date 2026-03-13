# UV-Vis Spectroscopy Peak Analysis CLI

## Overview
This skill helps create a robust Python CLI script for analyzing UV-Vis spectroscopy data, detecting peaks in absorption spectra, and outputting detailed analysis in JSON format with proper noise handling and data validation.

## Workflow
1. **Set up argument parsing** with required input/output files and optional parameters
2. **Load and validate CSV data** checking for common spectroscopy data issues
3. **Apply optional smoothing** to reduce noise using Savitzky-Golay or moving average filters
4. **Detect peaks** using scipy.signal.find_peaks with adaptive prominence based on noise level
5. **Calculate peak properties** including wavelength, height, FWHM, and baseline-corrected area
6. **Generate summary statistics** including dominant peak wavelength ranges
7. **Output results** in structured JSON format with validation warnings

## Common Pitfalls
- **Empty peaks list error**: Always check if peaks list is empty before calling max() function
- **Incorrect FWHM calculation**: Use scipy's peak_widths() instead of manual half-height calculation
- **Column detection issues**: Make detection flexible to handle various naming conventions (sample1, sample_1, absorbance)
- **Baseline integration error**: Subtract linear baseline between peak boundaries before integration
- **Noise peaks**: Apply smoothing and use adaptive prominence thresholds based on noise level
- **Index bounds errors**: Always validate array indices are within bounds before accessing

## Error Handling
- Wrap CSV loading in try-catch for file reading errors
- Check for required 'wavelength' column existence
- Validate data for NaN/infinite values, wavelength ordering, and irregular spacing
- Handle edge cases like single-point peaks and very short datasets
- Use fallback logic if peak_widths() function fails
- Filter out peaks that are too narrow (likely noise artifacts)

## Quick Reference
