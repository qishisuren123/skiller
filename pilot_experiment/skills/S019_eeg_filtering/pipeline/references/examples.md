# Adaptive filter order based on signal length
filter_order = min(4, len(data) // 30)
b, a = signal.butter(filter_order, [low, high], btype='band')

# Safe filtering with error handling
try:
    filtered_data[col] = signal.filtfilt(b, a, data[col])
except ValueError as e:
    print(f"Warning: Could not filter channel {col}: {e}")
    filtered_data[col] = data[col]  # Keep original

# Physiologically relevant frequency analysis
relevant_mask = (freqs >= 1.0) & (freqs <= 40.0)  # Exclude DC
alpha_mask = (freqs >= 8) & (freqs <= 13)  # Alpha band
total_mask = (freqs >= 1.0) & (freqs <= 40.0)  # Total power range

# JSON-safe conversion
analysis_serializable = convert_numpy_types(analysis)
with open('summary.json', 'w') as f:
    json.dump(analysis_serializable, f, indent=2)

# Input validation pattern
required_columns = ['time'] + [f'ch{i}' for i in range(1, 9)]
missing_columns = [col for col in required_columns if col not in data.columns]
if missing_columns:
    print(f"Error: Missing required columns: {missing_columns}")
    return False
