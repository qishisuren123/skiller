# Astronomical Light Curve Period Analysis with Lomb-Scargle

## Overview
This skill helps create a robust Python CLI script for analyzing astronomical light curves to detect periodic variability using the Lomb-Scargle periodogram method. It handles common pitfalls like aliasing, array length mismatches, and false alarm probability calculations.

## Workflow
1. **Parse command line arguments** for input/output files and period range
2. **Load and validate data** from CSV with proper error handling
3. **Clean data** by removing NaN values and applying consistent filtering
4. **Sort data by time** while maintaining array consistency across times, magnitudes, and errors
5. **Create frequency grid** respecting Nyquist limits and observation timespan
6. **Compute Lomb-Scargle periodogram** using scipy with proper normalization
7. **Apply harmonic analysis** to detect true fundamental periods vs aliases
8. **Calculate statistical significance** using proper false alarm probability
9. **Phase fold results** and compute amplitude and phase coverage metrics
10. **Output results** in structured JSON format with diagnostic information

## Common Pitfalls
- **Array length mismatches**: Always apply filtering and sorting operations consistently to all related arrays (times, magnitudes, errors)
- **Aliasing issues**: Harmonics can appear stronger than fundamental periods - use harmonic detection to find true periods
- **Incorrect FAP calculation**: Early versions used wrong statistical formulas - use proper effective frequency count
- **Nyquist violations**: Respect both median sampling rate and observation timespan limits
- **Missing astropy dependency**: Implement robust scipy-only solution with proper angular frequency handling
- **NaN handling**: Filter out invalid data points before any analysis to prevent downstream errors

## Error Handling
- **Data validation**: Check for minimum data points (≥10) before analysis
- **Array consistency**: Assert equal lengths after each filtering operation
- **Graceful degradation**: Return None for insufficient data rather than crashing
- **Debug output**: Print array lengths at each step to diagnose length mismatches
- **Exception handling**: Wrap main analysis in try-catch with informative error messages
- **Input validation**: Check file existence and required columns before processing

## Quick Reference
