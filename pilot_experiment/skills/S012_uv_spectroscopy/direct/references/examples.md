# Example 1: Basic peak detection for single sample
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, peak_widths

# Load UV-Vis data
df = pd.read_csv('uvvis_data.csv')
wavelength = df['wavelength'].values
absorbance = df['sample_1'].values

# Detect peaks with 0.1 minimum height, 10nm minimum separation
wavelength_spacing = np.mean(np.diff(wavelength))
peaks, _ = find_peaks(absorbance, height=0.1, distance=int(10/wavelength_spacing))

# Calculate FWHM
widths = peak_widths(absorbance, peaks, rel_height=0.5)
fwhm_values = widths[0] * wavelength_spacing

print(f"Found {len(peaks)} peaks")
for i, peak_idx in enumerate(peaks):
    print(f"Peak at {wavelength[peak_idx]:.1f} nm, FWHM: {fwhm_values[i]:.1f} nm")

# Example 2: Complete analysis with JSON output
results = {}
sample_columns = ['sample_1', 'sample_2', 'sample_3']

for sample in sample_columns:
    absorbance = df[sample].values
    peaks, _ = find_peaks(absorbance, height=0.1, distance=int(10/wavelength_spacing))
    
    if len(peaks) > 0:
        # Find dominant peak
        peak_heights = absorbance[peaks]
        dominant_idx = peaks[np.argmax(peak_heights)]
        
        results[sample] = {
            'n_peaks': len(peaks),
            'dominant_peak': {
                'wavelength': float(wavelength[dominant_idx]),
                'height': float(absorbance[dominant_idx])
            }
        }

import json
with open('peak_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)
