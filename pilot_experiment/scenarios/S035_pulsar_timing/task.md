# Pulsar Timing Analysis and Dispersion Measure Computation

Create a CLI script that processes pulsar timing observations to compute timing residuals and derive dispersion measure corrections. This task involves analyzing time-of-arrival (TOA) data from multiple radio frequencies to characterize pulsar spin behavior and interstellar medium effects.

Your script should accept timing data containing pulse arrival times at different observing frequencies and compute various timing statistics and corrections.

## Requirements

1. **Data Processing**: Parse input timing data containing columns for MJD (Modified Julian Date), frequency (MHz), TOA (time of arrival in seconds), and TOA uncertainty. Handle missing values and outliers (>5σ from median).

2. **Timing Model**: Implement a quadratic timing model: `predicted_TOA = T0 + P0*(pulse_number) + 0.5*P1*(pulse_number)^2`, where T0 is reference epoch, P0 is period, P1 is period derivative. Fit this model to the lowest frequency data to determine timing parameters.

3. **Dispersion Measure Calculation**: Compute frequency-dependent time delays using the cold plasma dispersion relation: `delay = K*DM/f^2`, where K=4.148808×10³ s·MHz²·pc⁻¹·cm³, DM is dispersion measure, f is frequency. Optimize DM to minimize timing residuals across all frequencies.

4. **Residual Analysis**: Calculate timing residuals (observed - predicted TOAs) after applying the timing model and dispersion corrections. Compute RMS residuals, reduced chi-squared, and identify systematic trends.

5. **Statistical Output**: Generate comprehensive statistics including: best-fit timing parameters with uncertainties, optimized dispersion measure, residual statistics by frequency band, and detection significance metrics.

6. **Data Export**: Save results to JSON file containing all derived parameters, residual statistics, and a CSV file with processed TOAs including residuals and corrections for each observation.

Use argparse for command-line interface with options for input data dimensions, output filenames, and analysis parameters.
