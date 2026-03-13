# Exoplanet Transit Detection and Fitting

Create a CLI script that detects and fits exoplanet transit signals in synthetic photometric time series data.

Your script should accept the following arguments:
- `--num_points`: Number of data points in the time series (default: 1000)
- `--noise_level`: Standard deviation of photometric noise (default: 0.001)
- `--transit_depth`: Expected transit depth as a fraction (default: 0.01)
- `--output_file`: Path to save results as JSON (required)
- `--plot_file`: Path to save diagnostic plot (optional)

## Requirements

1. **Generate synthetic photometric data**: Create a time series spanning 10 days with the specified number of points. Include a baseline flux of 1.0 with Gaussian noise at the specified level.

2. **Inject transit signal**: Add a realistic transit signal with the specified depth. The transit should have a duration of 3 hours, occur at day 5.0, and follow a simple box-car model (flat-bottomed).

3. **Detect transit**: Implement a basic transit detection algorithm using a sliding box-car filter. Calculate detection significance and identify the best-fit transit time.

4. **Fit transit parameters**: Perform a least-squares fit to determine the transit depth, duration, and center time. Use a simple box-car transit model for fitting.

5. **Output results**: Save results to JSON file containing: detected transit time, fitted depth, fitted duration, detection significance, and fit quality metrics (chi-squared, reduced chi-squared).

6. **Generate diagnostic plot** (if requested): Create a plot showing the original light curve, injected transit model, and best-fit model. Include residuals in a subplot.

The script should handle cases where no significant transit is detected and report appropriate error metrics.
