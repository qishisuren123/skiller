# Population Dynamics Modeling with Lotka-Volterra Equations

Create a CLI script that fits the Lotka-Volterra predator-prey model to time series data and generates population dynamics predictions.

The Lotka-Volterra equations describe the dynamics of biological systems with predator and prey populations:
- dx/dt = αx - βxy (prey equation)
- dy/dt = δxy - γy (predator equation)

Where x is prey population, y is predator population, and α, β, γ, δ are parameters to be estimated.

## Requirements

1. **Data Input**: Accept time series data via `--input` argument containing time, prey_population, and predator_population columns in CSV format.

2. **Parameter Estimation**: Fit the Lotka-Volterra model parameters (α, β, γ, δ) to the input data using numerical optimization. Handle the case where initial parameter guesses may need adjustment.

3. **Model Validation**: Calculate goodness-of-fit metrics including R² values for both prey and predator populations, and root mean square error (RMSE) for the overall fit.

4. **Prediction Generation**: Generate model predictions for a specified time range using `--predict_days` argument (default 100 days) beyond the input data timespan.

5. **Visualization Output**: Create a plot saved as `--output_plot` showing: original data points, fitted model curves, and future predictions with different line styles/colors for clarity.

6. **Results Export**: Save fitted parameters, goodness-of-fit metrics, and prediction data to a JSON file specified by `--output_results`.

The script should handle typical ecological data characteristics like noise and potential measurement gaps, providing robust parameter estimation even with imperfect data.

Example usage:
