#!/usr/bin/env python3
import argparse
import pandas as pd
import os
from pathlib import Path
import sys

def validate_frequency(freq_str):
    """Validate and normalize frequency string"""
    freq_mapping = {
        'min': 'T', 'mins': 'T', 'minute': 'T', 'minutes': 'T',
        'h': 'H', 'hr': 'H', 'hrs': 'H', 'hour': 'H', 'hours': 'H',
        'd': 'D', 'day': 'D', 'days': 'D'
    }
    
    import re
    match = re.match(r'(\d+)([a-zA-Z]+)', freq_str)
    if match:
        number, unit = match.groups()
        unit_lower = unit.lower()
        if unit_lower in freq_mapping:
            return f"{number}{freq_mapping[unit_lower]}"
    
    try:
        pd.Timedelta(freq_str)
        return freq_str
    except:
        raise ValueError(f"Invalid frequency format: {freq_str}. Use formats like '1H', '30T', '1D'")

def merge_station_data(input_dir, output_file, freq='1H'):
    """Merge and align multiple weather station CSV files"""
    
    freq = validate_frequency(freq)
    all_station_data = {}
    csv_files = list(Path(input_dir).glob('*.csv'))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in {input_dir}")
    
    processed_files = 0
    skipped_files = []
    
    # Process each file and separate by station_id
    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            
            if df.empty:
                print(f"Warning: Skipping empty file {file_path}")
                skipped_files.append(str(file_path))
                continue
            
            required_cols = ['timestamp', 'temperature', 'humidity', 'pressure', 'station_id']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                print(f"Warning: Skipping {file_path} - missing columns: {missing_cols}")
                skipped_files.append(str(file_path))
                continue
            
            try:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            except Exception as e:
                print(f"Warning: Skipping {file_path} - invalid timestamp format: {e}")
                skipped_files.append(str(file_path))
                continue
            
            df = df.dropna(subset=['timestamp'])
            if df.empty:
                print(f"Warning: Skipping {file_path} - no valid timestamps")
                skipped_files.append(str(file_path))
                continue
            
            processed_files += 1
            
            # Group by station_id within each file
            for station_id, station_group in df.groupby('station_id'):
                if pd.isna(station_id) or station_id == '':
                    print(f"Warning: Skipping rows with empty station_id in {file_path}")
                    continue
                    
                station_df = station_group.copy()
                station_df = station_df.set_index('timestamp')
                station_df = station_df.drop('station_id', axis=1)
                
                numeric_cols = station_df.select_dtypes(include=[float, int]).columns
                station_df = station_df[numeric_cols]
                
                if station_df.empty:
                    print(f"Warning: No numeric data for station {station_id} in {file_path}")
                    continue
                
                station_df.columns = [f"{station_id}_{col}" for col in station_df.columns]
                
                if station_id in all_station_data:
                    all_station_data[station_id] = pd.concat([all_station_data[station_id], station_df])
                else:
                    all_station_data[station_id] = station_df
                    
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            skipped_files.append(str(file_path))
            continue
    
    if not all_station_data:
        raise ValueError("No valid station data found in any files")
    
    print(f"Processed {processed_files} files successfully")
    if skipped_files:
        print(f"Skipped {len(skipped_files)} files due to errors")
    
    # Remove duplicates and sort by timestamp for each station
    for station_id in all_station_data:
        all_station_data[station_id] = all_station_data[station_id].sort_index().drop_duplicates()
    
    # Find common time range across all stations
    all_times = []
    for df in all_station_data.values():
        all_times.extend([df.index.min(), df.index.max()])
    
    start_time = min(all_times)
    end_time = max(all_times)
    
    # Create common time grid
    common_index = pd.date_range(start=start_time, end=end_time, freq=freq)
    
    # Resample each station to common grid
    resampled_data = []
    for station_id, df in all_station_data.items():
        resampled = df.resample(freq).mean().reindex(common_index)
        resampled_data.append(resampled)
    
    # Merge all dataframes
    merged_df = pd.concat(resampled_data, axis=1)
    
    # Handle missing values
    merged_df = merged_df.ffill(limit=3)
    merged_df = merged_df.bfill(limit=3)
    
    # Save to output file
    merged_df.to_csv(output_file)
    
    # Print summary statistics
    num_stations = len(all_station_data)
    time_range = f"{merged_df.index.min()} to {merged_df.index.max()}"
    total_values = merged_df.size
    missing_values = merged_df.isna().sum().sum()
    missing_percentage = (missing_values / total_values) * 100
    
    print(f"\nSummary:")
    print(f"  Number of stations: {num_stations}")
    print(f"  Time range: {time_range}")
    print(f"  Missing data percentage: {missing_percentage:.2f}%")
    print(f"  Resampling frequency: {freq}")
    print(f"Merged data saved to {output_file}")
    
    return merged_df

def main():
    parser = argparse.ArgumentParser(description='Merge weather station CSV files')
    parser.add_argument('--input-dir', required=True, help='Directory containing CSV files')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--freq', default='1H', help='Resampling frequency (e.g., 1H, 30min, 15T)')
    
    args = parser.parse_args()
    
    try:
        result = merge_station_data(args.input_dir, args.output, args.freq)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
