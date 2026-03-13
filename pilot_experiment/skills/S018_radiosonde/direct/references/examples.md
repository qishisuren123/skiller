# Example 1: Basic usage with sample data
"""
Sample CSV format (sounding.csv):
pressure,temperature,dewpoint,wind_speed,wind_direction,altitude
1013.2,15.2,12.1,5.2,180,100
1000.0,14.1,11.8,6.1,185,200
950.0,10.5,8.2,8.3,190,500
...

Command line usage:
python main.py --input sounding.csv --output results/
"""

# Example 2: Complete processing workflow
import pandas as pd
import numpy as np

# Load and process radiosonde data
df = pd.read_csv('example_sounding.csv')
df = df.sort_values('altitude').reset_index(drop=True)

# Calculate environmental lapse rates
lapse_rates = []
for i in range(len(df) - 1):
    dt = df.iloc[i+1]['temperature'] - df.iloc[i]['temperature']
    dz = df.iloc[i+1]['altitude'] - df.iloc[i]['altitude']
    lapse_rate = -dt / (dz / 1000) if dz > 0 else np.nan
    lapse_rates.append(lapse_rate)
lapse_rates.append(np.nan)
df['lapse_rate'] = lapse_rates

# Find tropopause (first level above 5km with lapse rate < 2°C/km)
above_5km = df[df['altitude'] >= 5000]
tropopause_candidates = above_5km[above_5km['lapse_rate'] < 2.0]
if len(tropopause_candidates) > 0:
    tropopause_height = tropopause_candidates.iloc[0]['altitude']
    tropopause_pressure = tropopause_candidates.iloc[0]['pressure']

print(f"Tropopause found at {tropopause_height} m, {tropopause_pressure} hPa")
