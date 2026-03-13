# Example 1: Basic station data alignment
import pandas as pd

# Load station data with proper datetime handling
df = pd.read_csv('station_A.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
df = df.set_index('timestamp').sort_index()

# Create hourly time grid and align
hourly_grid = pd.date_range(start='2023-01-01', end='2023-12-31', freq='1h')
df_aligned = df.reindex(hourly_grid)

# Apply missing value imputation
df_filled = df_aligned.fillna(method='ffill', limit=3).fillna(method='bfill', limit=3)

# Rename columns with station prefix
df_filled.columns = [f"station_A_{col}" for col in df_filled.columns]

# Example 2: Multi-station merge with validation
import os
from pathlib import Path

def merge_weather_stations(input_dir, output_file, freq='1h'):
    station_dfs = []
    
    # Process each CSV file
    for csv_file in Path(input_dir).glob("*.csv"):
        try:
            # Load and validate
            df = pd.read_csv(csv_file)
            required_cols = {'timestamp', 'temperature', 'humidity', 'pressure', 'station_id'}
            if not required_cols.issubset(set(df.columns)):
                print(f"Skipping {csv_file}: missing required columns")
                continue
            
            # Process timestamps and set index
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
            df = df.dropna(subset=['timestamp']).set_index('timestamp').sort_index()
            
            # Get station ID and prepare data
            station_id = df['station_id'].iloc[0]
            measurement_cols = ['temperature', 'humidity', 'pressure']
            df_clean = df[measurement_cols]
            
            station_dfs.append((df_clean, station_id))
            
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
    
    # Create common time grid
    all_indices = [df.index for df, _ in station_dfs]
    start_time = min(idx.min() for idx in all_indices)
    end_time = max(idx.max() for idx in all_indices)
    common_grid = pd.date_range(start=start_time, end=end_time, freq=freq)
    
    # Align and merge all stations
    aligned_dfs = []
    for df, station_id in station_dfs:
        # Resample and align
        df_resampled = df.resample(freq).mean().reindex(common_grid)
        df_filled = df_resampled.fillna(method='ffill', limit=3).fillna(method='bfill', limit=3)
        
        # Add station prefix to columns
        df_filled.columns = [f"{station_id}_{col}" for col in df_filled.columns]
        aligned_dfs.append(df_filled)
    
    # Combine and export
    merged_df = pd.concat(aligned_dfs, axis=1)
    merged_df.to_csv(output_file)
    
    return merged_df

# Usage
merged_data = merge_weather_stations('weather_data/', 'merged_stations.csv', '1h')
print(f"Merged data shape: {merged_data.shape}")
