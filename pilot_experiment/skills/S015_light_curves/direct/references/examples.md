# Example 1: Basic periodogram analysis
import numpy as np
from scipy.signal import lombscargle

# Simulate variable star data
t = np.sort(np.random.uniform(0, 100, 200))  # 200 random times over 100 days
true_period = 2.5
mags = 15.0 + 0.3 * np.sin(2*np.pi*t/true_period) + 0.05*np.random.randn(len(t))

# Compute periodogram
f_min, f_max = 1/10.0, 1/0.1  # Search 0.1 to 10 day periods
frequencies = np.linspace(f_min, f_max, 1000)
power = lombscargle(t, mags, 2*np.pi*frequencies, normalize=True)

# Find best period
best_idx = np.argmax(power)
detected_period = 1/frequencies[best_idx]
fap = 1 - (1 - np.exp(-power[best_idx]))**len(frequencies)

print(f"True period: {true_period:.2f} days")
print(f"Detected period: {detected_period:.2f} days") 
print(f"False alarm probability: {fap:.2e}")

# Example 2: Multi-band analysis structure
import pandas as pd

# Sample data structure
data = {
    'time': [1.0, 1.1, 2.0, 2.1, 3.0, 3.1],
    'magnitude': [15.2, 17.8, 15.1, 17.9, 15.3, 17.7], 
    'magnitude_error': [0.02, 0.05, 0.02, 0.05, 0.02, 0.05],
    'filter_band': ['V', 'I', 'V', 'I', 'V', 'I']
}
df = pd.DataFrame(data)

# Process each band separately
results = {}
for band in df['filter_band'].unique():
    df_band = df[df['filter_band'] == band]
    times = df_band['time'].values
    mags = df_band['magnitude'].values
    
    # Run periodogram analysis for this band
    # ... (periodogram code here)
    
    results[band] = {
        'best_period': 2.45,
        'significance': 1.2e-4,
        'amplitude': 0.25,
        'mean_magnitude': 15.2,
        'n_points': len(times),
        'phase_coverage': 0.85
    }
