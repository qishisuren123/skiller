# Frequency validation example
def validate_frequency(freq_str):
    freq_mapping = {'min': 'T', 'h': 'H', 'd': 'D'}
    match = re.match(r'(\d+)([a-zA-Z]+)', freq_str)
    if match:
        number, unit = match.groups()
        if unit.lower() in freq_mapping:
            return f"{number}{freq_mapping[unit.lower()]}"
    return freq_str

# Common time grid alignment
all_times = []
for df in station_data.values():
    all_times.extend([df.index.min(), df.index.max()])

start_time = min(all_times)
end_time = max(all_times)
common_index = pd.date_range(start=start_time, end=end_time, freq=freq)

# Robust file processing with error handling
for file_path in csv_files:
    try:
        df = pd.read_csv(file_path)
        if df.empty:
            print(f"Warning: Skipping empty file {file_path}")
            continue
        # Process file...
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        continue

# Station ID grouping and column renaming
for station_id, station_group in df.groupby('station_id'):
    station_df = station_group.set_index('timestamp')
    station_df = station_df.drop('station_id', axis=1)
    station_df.columns = [f"{station_id}_{col}" for col in station_df.columns]
