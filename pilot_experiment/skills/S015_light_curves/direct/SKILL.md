# Astronomical Light Curve Period Detection

## Overview
This skill enables detection of periodic variability in astronomical light curves using Lomb-Scargle periodogram analysis. It processes multi-band photometric time series data to identify dominant periods, assess their statistical significance, and characterize the variability properties for each filter band.

## Workflow
1. **Parse command line arguments** - Set up argparse with input CSV, output JSON, and period range parameters
2. **Load and validate photometric data** - Read CSV with time, magnitude, magnitude_error, and filter_band columns
3. **Group data by filter band** - Separate observations for independent analysis of each photometric band
4. **Compute Lomb-Scargle periodogram** - Calculate power spectrum over specified frequency range for each band
5. **Identify dominant periods** - Find peak power frequencies and convert to periods with false alarm probability assessment
6. **Phase-fold light curves** - Fold data at best period to calculate amplitude and phase coverage statistics
7. **Export results** - Save period detection results and variability characterization to JSON format

## Common Pitfalls
- **Insufficient frequency sampling**: Use at least 5x oversampling factor in periodogram to avoid missing narrow peaks
- **Ignoring Nyquist considerations**: For unevenly sampled data, maximum detectable frequency isn't simply 1/(2*dt_min)
- **Phase coverage bias**: Low phase coverage (<0.5) can create spurious period detections - always check phase_coverage metric
- **Magnitude vs flux confusion**: Astronomical magnitudes are logarithmic and inverted - larger magnitude = fainter source
- **Filter band contamination**: Ensure proper grouping by filter_band to avoid mixing different photometric systems

## Error Handling
- Validate CSV columns exist and contain numeric data types
- Handle empty filter bands gracefully with informative warnings
- Check for minimum data points (need ≥10 points for reliable periodogram)
- Catch scipy.signal errors for degenerate periodogram cases
- Implement file I/O error handling for input CSV and output JSON operations

## Quick Reference
