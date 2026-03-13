# Dose-Response Curve Analysis

## Overview
This skill enables fitting 4-parameter logistic (4PL) sigmoidal curves to dose-response data and computing key pharmacological parameters like IC50/EC50 values. Essential for drug potency analysis in pharmacology and toxicology research.

## Workflow
1. **Parse CLI arguments** for input CSV file and output directory paths using argparse
2. **Load and validate data** ensuring concentrations > 0 and responses in 0-100% range, filter invalid points
3. **Transform concentration data** to log10 scale for proper 4PL model fitting
4. **Fit 4-parameter logistic model** using scipy.optimize.curve_fit with appropriate initial parameter estimates
5. **Calculate pharmacological parameters** including IC50/EC50, Hill slope, top/bottom plateaus with confidence intervals
6. **Generate visualization** plotting original data points and fitted curve on semi-log axes
7. **Export results** saving fit parameters, statistics, and R-squared to JSON file

## Common Pitfalls
- **Poor initial parameter estimates**: Use data-driven estimates (min/max for plateaus, median concentration for IC50) to avoid convergence failures
- **Log transformation errors**: Handle zero/negative concentrations by filtering before log transformation, not after
- **Curve fitting divergence**: Set reasonable parameter bounds (IC50 within data range, Hill slope between -10 to 10) to prevent unrealistic fits
- **Confidence interval calculation**: Use parameter covariance matrix from curve_fit to compute standard errors, handle singular matrices gracefully
- **R-squared calculation**: Calculate using fitted values vs observed, not residuals, for proper goodness-of-fit assessment

## Error Handling
- Wrap file I/O operations in try-except blocks with informative error messages
- Check for sufficient data points (minimum 5-6) before attempting curve fitting
- Handle scipy optimization failures by trying different initial parameters or algorithms
- Validate that fitted IC50 falls within reasonable range of input concentrations

## Quick Reference
