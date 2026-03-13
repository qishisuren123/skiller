# Dose-Response Curve Analysis

Create a CLI script that analyzes dose-response data to fit sigmoidal curves and compute IC50/EC50 values. This is a common task in pharmacology and toxicology for determining drug potency.

Your script should accept concentration and response data, fit a 4-parameter logistic (4PL) model, and output key pharmacological parameters.

## Requirements

1. **Input Processing**: Accept two input arguments - a CSV file path containing dose-response data with columns 'concentration' and 'response', and an output directory path for results.

2. **Data Validation**: Ensure concentrations are positive numbers and responses are between 0-100 (representing % inhibition or % effect). Remove any invalid data points and report how many were filtered.

3. **Curve Fitting**: Fit a 4-parameter logistic model: `y = bottom + (top - bottom) / (1 + (x/ic50)^hill_slope)` where x is log10(concentration). Use scipy.optimize for fitting.

4. **Parameter Calculation**: Calculate and report the IC50/EC50 value (concentration at 50% response), Hill slope, top plateau, and bottom plateau values with their confidence intervals.

5. **Visualization**: Generate a plot showing the original data points and fitted curve. Use log scale for x-axis (concentration). Save as 'dose_response_curve.png' in the output directory.

6. **Results Export**: Save fitting parameters and statistics to 'fit_results.json' including IC50, Hill slope, R-squared goodness of fit, and the number of data points used.

Use argparse for command-line interface with arguments: `--input` (input CSV file), `--output` (output directory).

Example usage:
