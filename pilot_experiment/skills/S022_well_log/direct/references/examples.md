# Example 1: Basic usage with sample data
"""
Sample input CSV (well_log.csv):
depth,gamma_ray,resistivity,neutron_porosity,bulk_density,caliper
100.0,45.2,15.3,0.12,2.45,8.5
100.3,48.1,12.8,0.15,2.42,8.6
100.8,52.3,8.2,0.18,2.38,8.4
101.2,65.4,3.1,0.25,2.25,8.8

Command line usage:
python main.py --input well_log.csv --output results/ --depth-step 0.25

This produces:
- results/resampled_log.csv: uniform 0.25m sampling
- results/lithology_classification.csv: depth and lithology columns  
- results/summary.json: statistics and layer counts
"""

# Example 2: Handling data with gaps and quality issues
import pandas as pd
import numpy as np

# Create test data with realistic well log values
test_data = {
    'depth': [1000, 1000.5, 1001.2, 1001.8, 1002.5, 1003.1, 1003.7],
    'gamma_ray': [30, 45, 120, 135, 85, 40, 35],  # API units
    'resistivity': [25, 18, 2, 1.5, 8, 22, 28],   # ohm-m
    'neutron_porosity': [0.08, 0.12, 0.28, 0.32, 0.18, 0.10, 0.07],  # fraction
    'bulk_density': [2.55, 2.48, 2.15, 2.10, 2.35, 2.52, 2.58],      # g/cm3
    'caliper': [8.5, 8.6, 9.2, 9.8, 8.9, 8.4, 8.3]  # inches
}

df = pd.DataFrame(test_data)
df.to_csv('test_well_log.csv', index=False)

# Expected lithology classification results:
# depth 1000.0-1001.0: sandstone (low Vsh, good porosity, high resistivity)
# depth 1001.0-1002.0: shale (high Vsh from high gamma ray)
# depth 1002.0-1003.0: siltstone (intermediate properties)
# depth 1003.0+: limestone (high density, low neutron porosity, low Vsh)
