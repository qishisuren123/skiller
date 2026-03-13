#!/usr/bin/env python3
"""
Earth Observation Station Data Merger
Merges multiple weather station CSV files into a unified time-aligned dataset.
"""

import argparse
import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

def validate_csv_structure(filepath):
    """Validate that CSV has required columns."""
    required_cols = {'timestamp', 'temperature', 'humidity', 'pressure', 'station_id'}
    try:
        df = pd.read_csv(filepath, nrows=1)
        if not required_cols.issubset(set(df.columns)):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing columns: {missing}")
        return True
    except Exception as e:
        print(f"Warning: Skipping {filepath} - {e}")
        return False

def load_station_data(filepath):
    """Load and preprocess a single station's data."""
    try:
        df = pd.read_csv(filepath)
        
        # Convert timestamp to datetime with UTC timezone
        df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True, errors='coerce')
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['timestamp'])
        
        # Remove duplicate timestamps
        df = df.drop_duplicates(subset=['timestamp'])
        
        # Set timestamp as index
        df = df.set_index('timestamp').sort_index()
        
        # Extract station_id (assume consistent within file)
        station_id = df['station_id'].iloc[0]
        
        # Select only measurement columns
        measurement_cols = ['temperature', 'humidity', 'pressure']
        df = df[measurement_cols]
        
        return df, station_id
        
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return None, None

def create_common_time_grid(station_data_list, freq):
    """Create a common time index spanning all stations."""
    all_start_times = []
    all_end_times = []
    
    for df, _ in station_data_list:
        all_start_times.append(df.index.min())
        all_end_times.append(df.index.max())
    
    overall_start = min(all_start_times)
    overall_end = max(all_end_times)
    
    return pd.date_range(start=overall_start, end=overall_end, freq=freq)

def align_and_resample(df, station_id, common_index, freq):
    """Resample station data to common time grid and handle missing values."""
    # Resample to target frequency
    df_resampled = df.resample(freq).mean()
    
    # Align to common time grid
    df_aligned = df_resampled.reindex(common_index)
    
    # Apply missing value imputation
    df_filled = df_aligned.fillna(method='ffill', limit=3).fillna(method='bfill', limit=3)
    
    # Rename columns with station prefix
    df_filled.columns = [f"{station_id}_{col}" for col in df_filled.columns]
    
    return df_filled

def calculate_summary_stats(merged_df, station_count, time_range):
    """Calculate and print summary statistics."""
    total_values = merged_df.size
    missing_values = merged_df.isna().sum().sum()
    missing_percentage = (missing_values / total_values) * 100
    
    print(f"\n=== MERGE SUMMARY ===")
    print(f"Number of stations: {station_count}")
    print(f"Time range: {time_range[0]} to {time_range[1]}")
    print(f"Total data points: {total_values:,}")
    print(f"Missing values: {missing_values:,} ({missing_percentage:.2f}%)")
    print(f"Output shape: {merged_df.shape}")

def main():
    parser = argparse.ArgumentParser(
        description="Merge and align multiple weather station CSV files"
    )
    parser.add_argument(
        "--input-dir", 
        required=True, 
        help="Directory containing station CSV files"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Output CSV file path"
    )
    parser.add_argument(
        "--freq", 
        default="1h", 
        help="Resampling frequency (default: 1h)"
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_path = Path(args.input_dir)
    if not input_path.exists() or not input_path.is_dir():
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        sys.exit(1)
    
    # Validate frequency format
    try:
        pd.Timedelta(args.freq)
    except ValueError:
        print(f"Error: Invalid frequency format '{args.freq}'")
        print("Use pandas frequency strings like '1h', '30min', '1D'")
        sys.exit(1)
    
    # Discover CSV files
    csv_files = list(input_path.glob("*.csv"))
    if not csv_files:
        print(f"Error: No CSV files found in '{args.input_dir}'")
        sys.exit(1)
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Validate and load station data
    station_data = []
    for csv_file in csv_files:
        if validate_csv_structure(csv_file):
            df, station_id = load_station_data(csv_file)
            if df is not None:
                station_data.append((df, station_id))
                print(f"Loaded station '{station_id}': {len(df)} records")
    
    if not station_data:
        print("Error: No valid station data loaded")
        sys.exit(1)
    
    # Create common time grid
    print(f"\nCreating common time grid with frequency '{args.freq}'...")
    common_index = create_common_time_grid(station_data, args.freq)
    print(f"Time grid: {len(common_index)} time points")
    
    # Align and merge all stations
    print("Aligning and merging station data...")
    merged_dfs = []
    
    for df, station_id in station_data:
        aligned_df = align_and_resample(df, station_id, common_index, args.freq)
        merged_dfs.append(aligned_df)
    
    # Combine all stations
    final_df = pd.concat(merged_dfs, axis=1)
    
    # Export results
    print(f"Exporting to '{args.output}'...")
    final_df.to_csv(args.output)
    
    # Print summary
    time_range = (common_index.min(), common_index.max())
    calculate_summary_stats(final_df, len(station_data), time_range)
    
    print(f"\nMerge completed successfully!")

if __name__ == "__main__":
    main()
