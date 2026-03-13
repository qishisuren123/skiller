# Electrochemical Impedance Spectroscopy Circuit Fitting

Create a CLI script that fits equivalent circuit models to electrochemical impedance spectroscopy (EIS) data and analyzes the quality of different circuit topologies.

Your script should accept frequency-domain impedance data and fit multiple equivalent circuit models commonly used in electrochemistry. The script must implement complex nonlinear least squares fitting with proper weighting and provide comprehensive analysis of fitting quality.

## Requirements

1. **Data Processing**: Parse input impedance data containing frequency, real impedance (Z'), and imaginary impedance (Z'') columns. Handle data validation and preprocessing including outlier detection based on Kramers-Kronig relations.

2. **Circuit Implementation**: Implement at least 4 equivalent circuit models:
   - Simple RC parallel (R-RC)
   - Randles circuit (R-(RC)-W) with Warburg diffusion
   - Double layer circuit (R-RC-RC) with two time constants  
   - Constant Phase Element circuit (R-RC_CPE) where CPE replaces ideal capacitor

3. **Complex Fitting Algorithm**: Implement weighted complex nonlinear least squares fitting using Levenberg-Marquardt or similar algorithm. Weight data points appropriately (typically by |Z|^-1) and handle both real and imaginary components simultaneously.

4. **Statistical Analysis**: Calculate comprehensive fitting statistics including chi-squared, reduced chi-squared, R-squared for both real and imaginary parts, parameter uncertainties, and correlation matrix. Implement F-test for model comparison.

5. **Model Selection**: Automatically determine the best-fitting circuit model using information criteria (AIC/BIC) while penalizing overfitting. Provide ranking of all tested models with statistical justification.

6. **Output Generation**: Generate detailed JSON results containing fitted parameters with uncertainties, goodness-of-fit metrics, model rankings, and residual analysis. Create optional Nyquist and Bode plots showing experimental data, fitted curves, and residuals.

The script should be robust to different data qualities and provide meaningful error messages for problematic datasets.
