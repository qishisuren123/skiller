1. Initialize PulsarTimingAnalyzer with input CSV file path
2. Load timing data and validate required columns (MJD, frequency, TOA, uncertainty)
3. Remove statistical outliers using 5σ threshold based on median absolute deviation
4. Filter data to lowest frequency band for timing model fitting
5. Convert MJD timestamps to pulse numbers using reference epoch
6. Fit quadratic timing model using scipy.optimize.curve_fit with initial parameter estimates
7. Extract timing parameters (T0, P0, P1) and uncertainties from covariance matrix
8. Optimize dispersion measure using Nelder-Mead minimization to minimize residual RMS
9. Calculate final timing residuals with dispersion corrections applied
10. Compute comprehensive statistics including reduced chi-squared and frequency band analysis
11. Export results to JSON format with timing parameters and residual statistics
12. Save processed data to CSV with residuals and predicted TOAs
