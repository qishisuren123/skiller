# Example 1: Basic 4PL curve fitting
import numpy as np
from scipy.optimize import curve_fit

def four_pl_model(log_conc, bottom, top, log_ic50, hill_slope):
    return bottom + (top - bottom) / (1 + 10**((log_ic50 - log_conc) * hill_slope))

# Sample data
concentrations = np.array([1e-9, 1e-8, 1e-7, 1e-6, 1e-5, 1e-4])
responses = np.array([95, 90, 75, 50, 25, 10])
log_conc = np.log10(concentrations)

# Fit curve
p0 = [5, 95, -6, 1]  # [bottom, top, log_ic50, hill_slope]
popt, pcov = curve_fit(four_pl_model, log_conc, responses, p0=p0)
ic50 = 10**popt[2]
print(f"IC50: {ic50:.2e} M")

# Example 2: Complete analysis with error handling
import pandas as pd
import matplotlib.pyplot as plt

# Load and validate data
df = pd.read_csv('dose_response.csv')
df_clean = df[(df['concentration'] > 0) & (df['response'].between(0, 100))]

# Fit with bounds
bounds = ([0, 50, -12, -10], [50, 100, -3, 10])
try:
    popt, pcov = curve_fit(four_pl_model, np.log10(df_clean['concentration']), 
                          df_clean['response'], bounds=bounds)
    
    # Calculate confidence intervals
    param_errors = np.sqrt(np.diag(pcov))
    ic50_ci = 10**(popt[2] + np.array([-1.96, 1.96]) * param_errors[2])
    
    print(f"IC50: {10**popt[2]:.2e} M (95% CI: {ic50_ci[0]:.2e} - {ic50_ci[1]:.2e})")
    
except Exception as e:
    print(f"Fitting failed: {e}")
