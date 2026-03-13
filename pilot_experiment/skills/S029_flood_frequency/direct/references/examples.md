# Example 1: Basic GEV fitting and return period calculation
import numpy as np
from scipy.stats import genextreme

# Sample annual maxima data
annual_maxima = np.array([45.2, 67.8, 123.4, 89.1, 156.7, 78.9, 234.5, 98.2, 145.6, 187.3])

# Fit GEV distribution
shape, loc, scale = genextreme.fit(annual_maxima)
print(f"GEV Parameters - Shape: {shape:.3f}, Location: {loc:.1f}, Scale: {scale:.1f}")

# Calculate return period discharges
return_periods = [10, 50, 100]
for T in return_periods:
    q_t = genextreme.ppf(1 - 1/T, shape, loc=loc, scale=scale)
    print(f"{T}-year flood: {q_t:.1f} cms")

# Example 2: Digital baseflow filter implementation
import pandas as pd
import numpy as np

# Sample daily discharge data
dates = pd.date_range('2020-01-01', periods=365, freq='D')
discharge = np.random.lognormal(3, 0.5, 365)  # Simulated discharge data

# Apply baseflow filter
alpha = 0.925
baseflow = np.zeros_like(discharge)
baseflow[0] = discharge[0]

for i in range(1, len(discharge)):
    filtered_value = alpha * baseflow[i-1] + (1-alpha)/2 * (discharge[i] + discharge[i-1])
    baseflow[i] = min(filtered_value, discharge[i])

quickflow = discharge - baseflow

# Create results dataframe
results = pd.DataFrame({
    'date': dates,
    'discharge_cms': discharge,
    'baseflow_cms': baseflow,
    'quickflow_cms': quickflow
})

print(f"Mean baseflow index: {baseflow.mean()/discharge.mean():.3f}")
