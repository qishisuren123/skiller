# XRD Pattern Analysis

## Overview
This skill enables analysis of X-ray diffraction (XRD) patterns by performing background subtraction, peak detection, Gaussian fitting, and d-spacing calculations using Bragg's law. It processes CSV data and outputs comprehensive analysis results.

## Workflow
1. **Parse command line arguments** - Set up input file, output directory, wavelength, and peak detection parameters
2. **Load and validate XRD data** - Read CSV file with two_theta and intensity columns, check data quality
3. **Perform background subtraction** - Apply rolling minimum with large window, smooth the background, subtract from raw data
4. **Detect peaks** - Use scipy.signal.find_peaks on background-corrected data with height and prominence thresholds
5. **Fit Gaussian peaks** - For each detected peak, fit Gaussian function to extract position, amplitude, and width
6. **Calculate d-spacings** - Apply Bragg's law: d = λ/(2*sin(θ)) where θ = two_theta/2
7. **Generate outputs** - Save peaks.csv, fitted_pattern.csv, summary.json and print key results

## Common Pitfalls
- **Insufficient background window size** - Rolling minimum window too small fails to capture broad background features. Solution: Use window ≥50 points, adjust based on data density
- **Peak fitting convergence failures** - Gaussian fits may fail on noisy or overlapping peaks. Solution: Set reasonable initial parameters and bounds, handle optimization exceptions gracefully
- **Angle unit confusion** - Mixing degrees and radians in Bragg's law calculations. Solution: Always convert two_theta from degrees to radians before trigonometric functions
- **Edge effects in rolling operations** - Rolling minimum creates NaN values at edges. Solution: Use pandas rolling with min_periods=1 or handle edge cases explicitly
- **Overlapping peak regions** - Gaussian fits on overlapping peaks give poor results. Solution: Define fitting windows around each peak (±3*estimated_width)

## Error Handling
- Validate input CSV format and required columns before processing
- Handle scipy.optimize curve fitting failures with try-except blocks
- Check for sufficient data points around each peak before fitting
- Validate physical parameters (positive wavelength, reasonable two_theta range 5-90°)
- Create output directory if it doesn't exist, handle file write permissions

## Quick Reference
