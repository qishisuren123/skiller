#!/usr/bin/env python3
import argparse
import pandas as pd
import os
import glob
import warnings
import logging
import sys
from pathlib import Path

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('merge_stations.log')
        ]
    )

def parse_arguments():
    parser = argparse.ArgumentParser(description='Merge and align Earth observation station CSV files')
    parser.add_argument('--input-dir', required=True, help='Directory containing CSV files')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--freq', default='1H', help='Resampling frequency (default: 1H for hourly)')
    return parser.parse_args()

def read_station_files(input_dir):
    """Read all CSV files from the input directory"""
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")
    
    csv_files = glob.glob(os.path.join(input_dir, '*.csv'))
    
    if not csv_files:
        raise ValueError(f"No CSV files found in directory: {input_dir}")
    
    logging.info(f"Found {len(csv_files)} CSV files to process")
    
    station_data = []
    failed_files = []
    
    for file_path in csv_files:
        try:
            logging.info(f"Reading {file_path}")
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_cols = ['timestamp', 'temperature', 'humidity', 'pressure', 'station_id']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                logging.warning(f"File {file_path} missing columns: {missing_cols}. Skipping.")
                failed_files.append(file_path)
                continue
            
            # Check if file is empty
            if df.empty:
                logging.warning(f"File {file_path} is empty. Skipping.")
                failed_files.append(file_path)
                continue
            
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            station_data.append(df)
            logging.info(f"Successfully loaded {file_path}: {df.shape[0]} records")
            
        except Exception as e:
            logging.error(f"Failed to read {file_path}: {str(e)}")
            failed_files.append(file_path)
            continue
    
    if not station_data:
        raise ValueError("No valid CSV files could be processed")
    
    if failed_files:
        logging.warning(f"Failed to process {len(failed_files)} files: {failed_files}")
    
    return station_data

def align_and_merge(station_data, freq):
    """Align stations to common time grid and merge using memory-efficient approach"""
    try:
        # Find union of time ranges
        start_time = min([df.index.min() for df in station_data])
        end_time = max([df.index.max() for df in station_data])
        
        logging.info(f"Overall time range: {start_time} to {end_time}")
        
        # Process each station separately and collect DataFrames for concatenation
        processed_dfs = []
        
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*freq.*resample.*", category=FutureWarning)
            
            for df in station_data:
                try:
                    station_id = df['station_id'].iloc[0]
                    logging.info(f"Processing station {station_id}, original shape: {df.shape}")
                    
                    # Make a copy to avoid modifying original data
                    df_copy = df.copy()
                    
                    # Resample to common frequency
                    resampled = df_copy.resample(freq).mean()
                    
                    # Create new DataFrame with renamed columns
                    station_df = pd.DataFrame(index=resampled.index)
                    
                    for col in ['temperature', 'humidity', 'pressure']:
                        if col in resampled.columns:
                            new_col_name = f'{station_id}_{col}'
                            station_df[new_col_name] = resampled[col].copy()
                            
                            # Add data validation
                            sample_values = station_df[new_col_name].dropna().head(3)
                            logging.debug(f"  {new_col_name}: sample values = {sample_values.tolist()}")
                    
                    if len(station_df.columns) > 0:
                        processed_dfs.append(station_df)
                        logging.info(f"Station {station_id}: {len(station_df.columns)} columns prepared")
                    else:
                        logging.warning(f"Station {station_id}: No valid data columns found")
                        
                except Exception as e:
                    logging.error(f"Failed to process station data: {str(e)}")
                    continue
        
        if not processed_dfs:
            raise ValueError("No station data could be processed successfully")
        
        # Use concat with outer join to merge all stations efficiently
        logging.info("Concatenating all station data...")
        merged_df = pd.concat(processed_dfs, axis=1, join='outer', sort=True)
        
        # Ensure we cover the full time range
        full_index = pd.date_range(start=start_time, end=end_time, freq=freq)
        merged_df = merged_df.reindex(full_index)
        
        return merged_df
        
    except Exception as e:
        logging.error(f"Error in align_and_merge: {str(e)}")
        raise

def main():
    args = parse_arguments()
    
    # Set up logging
    setup_logging()
    
    try:
        # Read station files
        logging.info("Reading station files...")
        station_data = read_station_files(args.input_dir)
        
        # Align and merge data
        logging.info("Aligning and merging data...")
        merged_data = align_and_merge(station_data, args.freq)
        
        # Calculate missing data percentage BEFORE filling
        logging.info("Calculating statistics...")
        total_values = merged_data.size
        missing_values_before = merged_data.isna().sum().sum()
        missing_percentage_before = (missing_values_before / total_values) * 100
        
        # Handle missing values
        logging.info("Filling missing values...")
        merged_data = merged_data.ffill(limit=3)
        merged_data = merged_data.bfill(limit=3)
        
        # Calculate missing data percentage AFTER filling
        missing_values_after = merged_data.isna().sum().sum()
        missing_percentage_after = (missing_values_after / total_values) * 100
        
        # Save output
        logging.info(f"Saving to {args.output}...")
        merged_data.to_csv(args.output)
        
        print(f"\nSummary:")
        print(f"Merged data from {len(station_data)} stations")
        print(f"Output shape: {merged_data.shape}")
        print(f"Time range: {merged_data.index.min()} to {merged_data.index.max()}")
        print(f"Missing data before filling: {missing_percentage_before:.2f}%")
        print(f"Missing data after filling: {missing_percentage_after:.2f}%")
        
        logging.info("Processing completed successfully")
        
    except Exception as e:
        logging.error(f"Script failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
