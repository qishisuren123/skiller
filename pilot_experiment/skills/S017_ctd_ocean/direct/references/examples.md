# Example 1: Basic CTD profile processing
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# Load sample CTD data
ctd_data = pd.DataFrame({
    'station_id': ['CTD001'] * 10,
    'depth_m': [0, 5, 10, 20, 30, 50, 75, 100, 150, 200],
    'temperature_C': [15.2, 15.1, 14.8, 12.5, 10.2, 8.1, 6.5, 5.2, 4.1, 3.8],
    'salinity_PSU': [34.1, 34.2, 34.3, 34.5, 34.7, 34.8, 34.9, 35.0, 35.1, 35.1],
    'dissolved_oxygen_mL_L': [6.2, 6.1, 5.9, 5.5, 4.8, 4.2, 3.8, 3.5, 3.2, 3.0]
})

# Interpolate to 1-meter resolution
depths = ctd_data['depth_m'].values
max_depth = depths.max()
depth_grid = np.arange(0, max_depth + 1, 1.0)

# Interpolate temperature
f_temp = interp1d(depths, ctd_data['temperature_C'], kind='linear')
temp_interp = f_temp(depth_grid)

# Calculate potential density (sigma-t)
f_sal = interp1d(depths, ctd_data['salinity_PSU'], kind='linear')
sal_interp = f_sal(depth_grid)
sigma_t = -0.093 + 0.808*sal_interp - 0.0016*sal_interp**2 + (-0.0069 + 0.0025*sal_interp)*temp_interp - 0.0001*temp_interp**2

# Find thermocline depth
dt_dz = np.gradient(temp_interp, depth_grid)
thermocline_idx = np.argmax(np.abs(dt_dz[1:-1])) + 1
thermocline_depth = depth_grid[thermocline_idx]

print(f"Thermocline depth: {thermocline_depth:.1f} m")

# Example 2: Complete CLI usage pattern
"""
# Create sample CTD dataset
python -c "
import pandas as pd
import numpy as np

# Generate synthetic CTD data for multiple stations
stations = []
for stn in ['CTD001', 'CTD002', 'CTD003']:
    depths = np.array([0, 5, 10, 20, 30, 50, 75, 100, 150, 200, 250])
    # Realistic temperature profile with thermocline
    temps = 16 - 0.05*depths - 0.0001*depths**2
    # Typical salinity profile
    sals = 34.0 + 0.004*depths
    # Oxygen minimum zone
    o2 = 6.0 - 0.01*depths + 0.00002*depths**2
    
    station_data = pd.DataFrame({
        'station_id': stn,
        'depth_m': depths,
        'temperature_C': temps + np.random.normal(0, 0.1, len(depths)),
        'salinity_PSU': sals + np.random.normal(0, 0.05, len(depths)),
        'dissolved_oxygen_mL_L': o2 + np.random.normal(0, 0.1, len(depths))
    })
    stations.append(station_data)

ctd_dataset = pd.concat(stations, ignore_index=True)
ctd_dataset.to_csv('sample_ctd_data.csv', index=False)
print('Created sample_ctd_data.csv')
"

# Run the CTD processing script
python main.py --input sample_ctd_data.csv --output ./ctd_results --depth-resolution 2.0

# Expected output files:
# ./ctd_results/interpolated_profiles.csv - All stations interpolated to 2m resolution
# ./ctd_results/station_summary.json - Thermocline and mixed layer depths per station
"""
