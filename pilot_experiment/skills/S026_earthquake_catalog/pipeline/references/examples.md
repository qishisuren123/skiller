# Robust division check pattern
denominator = mean_mag - min_mag + delta_bin/2
if denominator <= 0:
    return None, completeness_mag
result = numerator / denominator

# Column validation pattern
required_columns = ['event_id', 'latitude', 'longitude']
missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    print(f"Error: Missing columns: {', '.join(missing_columns)}")
    return

# Reverse cumulative calculation
cumulative = []
for i in range(len(hist)):
    cum_count = np.sum(hist[i:])  # Sum from current bin to end
    cumulative.append(cum_count)

# Preventing double classification
used_items = set()
for item in sorted_items:
    if item.id in used_items:
        continue
    # Process item
    used_items.add(related_item.id)
