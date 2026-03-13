# Water year calculation (corrected)
station_data['water_year'] = station_data['date'].dt.year
mask = station_data['date'].dt.month >= 10
station_data.loc[mask, 'water_year'] = station_data.loc[mask, 'date'].dt.year + 1

# Digital filter with gap handling
valid_indices = np.where(valid_mask)[0]
segment_starts = [valid_indices[0]]
for i in range(1, len(valid_indices)):
    if valid_indices[i] - valid_indices[i-1] > 1:  # Gap detected
        segment_starts.append(valid_indices[i])

# Robust GEV fitting with fallback
try:
    shape, loc, scale = stats.genextreme.fit(station_max, method='MLE')
    if scale <= 0:
        raise ValueError("Invalid scale parameter")
except (stats.FitSolverError, ValueError) as e:
    shape, loc, scale = stats.genextreme.fit(station_max, method='MM')

# Flood frequency calculation with validation
prob = 1 - 1/T  # Return period T to probability
Q_T = stats.genextreme.ppf(prob, shape, loc=loc, scale=scale)
ratio_to_max = Q_T / max_observed
if ratio_to_max > 5.0:
    print(f"Warning: Unrealistic estimate detected")

# Digital filter implementation
filter_value = alpha * baseflow[t-1] + (1-alpha)/2 * (Q[t] + Q[t-1])
baseflow[t] = min(filter_value, Q[t])  # Integrated clipping
