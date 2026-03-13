# Exoplanet Transit Detection and Fitting

## Overview
This skill enables detection and parameter fitting of exoplanet transit signals in photometric time series data using box-car filtering and least-squares optimization. It handles synthetic data generation, signal injection, detection algorithms, and diagnostic visualization for transit photometry analysis.

## Workflow
1. **Generate baseline photometric time series** with specified sampling, noise characteristics, and 10-day observation window
2. **Inject realistic box-car transit signal** at day 5.0 with specified depth and 3-hour duration using proper transit geometry
3. **Apply sliding box-car detection filter** across time series to identify transit candidates and calculate detection significance
4. **Perform least-squares parameter fitting** using box-car transit model to estimate depth, duration, and center time
5. **Calculate fit quality metrics** including chi-squared, reduced chi-squared, and parameter uncertainties
6. **Generate diagnostic plots** showing light curve, models, and residuals with proper astronomical formatting
7. **Export results to structured JSON** with detection metrics, fitted parameters, and quality assessments

## Common Pitfalls
- **Inadequate time sampling around transit**: Ensure sufficient data points during 3-hour transit window by using proper time grid spacing, especially for sparse sampling
- **Box-car filter edge effects**: Pad time series or restrict search window to avoid spurious detections at data boundaries where filter response is unreliable
- **Poor initial parameter estimates**: Use detection results to seed fitting algorithm with reasonable starting values to avoid local minima in parameter space
- **Ignoring photometric noise correlation**: Account for potential time-correlated noise when calculating detection significance and parameter uncertainties
- **Unrealistic transit geometry**: Ensure transit duration and depth are physically consistent and box-car model approximation is valid for the signal-to-noise regime

## Error Handling
- Validate that transit duration (3 hours) is properly sampled given the number of data points and 10-day baseline
- Check for convergence failures in least-squares fitting and provide fallback parameter estimates
- Handle cases where no significant transit is detected (significance < 3σ) by reporting null results
- Verify output file paths are writable and handle JSON serialization errors for numpy data types
- Catch and report numerical issues in chi-squared calculations when noise levels are extremely low

## Quick Reference
