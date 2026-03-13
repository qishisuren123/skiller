# Example 1: Basic power spectrum computation
import numpy as np

# Generate synthetic CMB map (1024 pixels, NSIDE=16)
nside = 16
npix = 12 * nside**2
temp_map = np.random.normal(0, 100, npix)  # 100 μK RMS

# Save test data
np.save('test_cmb_map.npy', temp_map)

# Run analysis
# python main.py test_cmb_map.npy --output-json results.json --output-plot spectrum.png

# Example 2: Processing with custom parameters
import json

# Load and analyze with specific lmax
temp_map = np.load('high_res_cmb.npy')
nside = int(np.sqrt(len(temp_map) / 12))
custom_lmax = min(100, 2 * nside)  # Conservative limit

# Command: python main.py high_res_cmb.npy --lmax 100 --output-json custom_results.json

# Load results for further analysis
with open('results.json', 'r') as f:
    data = json.load(f)
    
multipoles = np.array(data['multipoles'])
cl = np.array(data['power_spectrum'])
stats = data['statistics']

print(f"Peak power at l={stats['peak_multipole']}: {stats['peak_power']:.2e} μK²")
