# Fatigue Life Analysis Tool

Create a command-line tool that analyzes fatigue test data to fit S-N (stress-number of cycles) curves and predict fatigue life for materials under cyclic loading.

The S-N curve is a fundamental relationship in fatigue analysis that describes how the stress amplitude (S) relates to the number of cycles to failure (N). The relationship typically follows a power law: S = A * N^(-b), where A and b are material-dependent constants.

Your script should accept fatigue test data containing stress amplitudes and corresponding cycles to failure, then fit an S-N curve to predict fatigue life at different stress levels.

## Requirements

1. **Data Input**: Accept stress amplitude and cycles-to-failure data via command-line arguments specifying input format (stress values and cycle counts as comma-separated lists or ranges).

2. **S-N Curve Fitting**: Fit the power law relationship S = A * N^(-b) to the input data using log-linear regression (log(S) vs log(N)). Calculate and report the fitting parameters A and b with their R-squared correlation coefficient.

3. **Fatigue Life Prediction**: For a given set of stress levels, predict the expected cycles to failure using the fitted S-N curve. Handle both single stress values and stress ranges.

4. **Endurance Limit**: Estimate the endurance limit (stress level below which the material theoretically has infinite life) by extrapolating the S-N curve to a high cycle count (typically 10^7 cycles for steel).

5. **Output Generation**: Save results to a JSON file containing fitted parameters, R-squared value, endurance limit, and predictions. Also generate a matplotlib plot showing the original data points, fitted S-N curve, and prediction points.

6. **Statistical Analysis**: Calculate 95% confidence intervals for the fitted curve and include safety factors in predictions (typically 2x reduction in predicted life for engineering applications).

The tool should handle typical fatigue testing scenarios and provide reliable predictions for engineering design applications.
