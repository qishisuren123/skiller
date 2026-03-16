#!/usr/bin/env python3
"""
Sea Surface Temperature Anomaly Analysis Tool
Processes SST data to compute temperature anomalies and generate statistics.
"""

import argparse
import numpy as np
import json
import csv
import logging
import time
from pathlib import Path

def setup_logging(log_level, log_file=None):
    """Setup logging configuration."""
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[]
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(log_format))
    logging.getLogger().addHandler(console_handler)
    
    # Add file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(log_format))
        logging.getLogger().addHandler(file_handler)
        logging.info(f"Logging to file: {log_file}")

def generate_synthetic_sst(rows, cols, seed=42):
    """Generate synthetic SST data with realistic ocean temperature patterns."""
    logging.info(f"Generating synthetic SST data with shape ({rows}, {cols}) and seed {seed}")
    np.random.seed(seed)
    
    # Create base temperature field with latitudinal gradient
    lat_gradient = np.linspace(28, 2, rows)  # Warmer at equator
    base_temp = np.tile(lat_gradient, (cols, 1)).T
    
    # Add random variations and some spatial correlation
    noise = np.random.normal(0, 2, (rows, cols))
    # Simple smoothing for spatial correlation
    for i in range(1, rows-1):
        for j in range(1, cols-1):
            noise[i,j] = 0.5 * noise[i,j] + 0.5 * np.mean(noise[i-1:i+2, j-1:j+2])
    
    sst_data = base_temp + noise
    logging.info(f"Synthetic data generated: min={np.min(sst_data):.2f}°C, max={np.max(sst_data):.2f}°C")
    return sst_data

def load_sst_data(filepath):
    """Load SST data from numpy .npy file."""
    logging.info(f"Loading SST data from {filepath}")
    try:
        data = np.load(filepath)
        if data.ndim != 2:
            raise ValueError(f"Expected 2D array, got {data.ndim}D array")
        logging.info(f"Successfully loaded data with shape {data.shape}")
        return data
    except Exception as e:
        logging.error(f"Error loading SST data from {filepath}: {e}")
        raise ValueError(f"Error loading SST data from {filepath}: {e}")

def compute_anomalies(sst_data):
    """Compute SST anomalies relative to spatial mean climatology, handling NaN values."""
    logging.info("Computing SST anomalies relative to climatological mean")
    
    # Use nanmean to ignore NaN values in climatology calculation
    climatology = np.nanmean(sst_data)
    logging.info(f"Climatological mean: {climatology:.3f}°C")
    
    anomalies = sst_data - climatology
    logging.debug(f"Anomaly range: {np.nanmin(anomalies):.3f} to {np.nanmax(anomalies):.3f}°C")
    
    return anomalies, climatology

def analyze_anomalies(anomalies):
    """Generate comprehensive statistics for SST anomalies, handling NaN values."""
    logging.info("Computing anomaly statistics")
    start_time = time.time()
    
    # Check for valid data points first
    valid_mask = ~np.isnan(anomalies)
    valid_points = np.sum(valid_mask)
    total_points = anomalies.size
    
    if valid_points == 0:
        logging.warning("No valid data points found!")
        return {
            'mean_anomaly': float('nan'),
            'std_anomaly': float('nan'),
            'max_anomaly': float('nan'),
            'min_anomaly': float('nan'),
            'valid_data_points': 0,
            'total_data_points': int(total_points),
            'data_coverage_pct': 0.0,
            'pct_above_1c': 0.0,
            'pct_above_2c': 0.0,
            'max_anomaly_location': [0, 0],
            'min_anomaly_location': [0, 0]
        }
    
    stats = {
        'mean_anomaly': float(np.nanmean(anomalies)),
        'std_anomaly': float(np.nanstd(anomalies)),
        'max_anomaly': float(np.nanmax(anomalies)),
        'min_anomaly': float(np.nanmin(anomalies))
    }
    
    stats['valid_data_points'] = int(valid_points)
    stats['total_data_points'] = int(total_points)
    stats['data_coverage_pct'] = float(valid_points / total_points * 100)
    
    logging.info(f"Data coverage: {stats['data_coverage_pct']:.1f}% ({valid_points}/{total_points} points)")
    
    # Threshold analysis - only count valid points
    valid_anomalies = anomalies[valid_mask]
    above_1c = np.sum(np.abs(valid_anomalies) > 1.0)
    above_2c = np.sum(np.abs(valid_anomalies) > 2.0)
    
    stats['pct_above_1c'] = float(above_1c / valid_points * 100)
    stats['pct_above_2c'] = float(above_2c / valid_points * 100)
    
    logging.info(f"Extreme anomalies: {stats['pct_above_1c']:.1f}% >1°C, {stats['pct_above_2c']:.1f}% >2°C")
    
    # Find extreme locations - handle edge cases
    try:
        max_idx = np.unravel_index(np.nanargmax(anomalies), anomalies.shape)
        min_idx = np.unravel_index(np.nanargmin(anomalies), anomalies.shape)
        stats['max_anomaly_location'] = [int(max_idx[0]), int(max_idx[1])]
        stats['min_anomaly_location'] = [int(min_idx[0]), int(min_idx[1])]
        logging.debug(f"Max anomaly at {max_idx}, min anomaly at {min_idx}")
    except ValueError:
        # Handle case where all values are identical (all anomalies are 0 or NaN)
        logging.warning("Cannot determine extreme locations - uniform field detected")
        stats['max_anomaly_location'] = [0, 0]
        stats['min_anomaly_location'] = [0, 0]
    
    elapsed = time.time() - start_time
    logging.info(f"Statistics computed in {elapsed:.2f} seconds")
    return stats

def main():
    parser = argparse.ArgumentParser(description='Analyze SST anomalies')
    parser.add_argument('--input-file', type=str, help='Input .npy file with SST data')
    parser.add_argument('--rows', type=int, default=50, help='Grid rows (for synthetic data)')
    parser.add_argument('--cols', type=int, default=100, help='Grid columns (for synthetic data)') 
    parser.add_argument('--output-json', default='sst_stats.json', help='JSON output file')
    parser.add_argument('--output-csv', default='sst_anomalies.csv', help='CSV anomaly file')
    parser.add_argument('--skip-csv', action='store_true', help='Skip CSV output for large datasets')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    parser.add_argument('--log-file', type=str, help='Log file path')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logging.info("Starting SST anomaly analysis")
    
    # Load or generate SST data
    if args.input_file:
        sst_data = load_sst_data(args.input_file)
        nan_count = np.sum(np.isnan(sst_data))
        logging.info(f"NaN values: {nan_count} ({nan_count/sst_data.size*100:.1f}%)")
    else:
        sst_data = generate_synthetic_sst(args.rows, args.cols)
    
    # Compute anomalies
    anomalies, climatology = compute_anomalies(sst_data)
    
    # Check for uniform field
    if np.nanstd(sst_data) == 0:
        logging.warning("Uniform temperature field detected - all anomalies will be zero")
    
    # Analyze
    stats = analyze_anomalies(anomalies)
    stats['climatology'] = float(climatology)
    stats['data_shape'] = list(sst_data.shape)
    
    # Save results
    logging.info(f"Saving JSON results to {args.output_json}")
    with open(args.output_json, 'w') as f:
        json.dump(stats, f, indent=2)
    
    # Save anomalies as CSV only if requested
    if not args.skip_csv:
        logging.info(f"Writing CSV file to {args.output_csv}")
        csv_start = time.time()
        with open(args.output_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            for row in anomalies:
                writer.writerow(row.tolist())
        logging.info(f"CSV written in {time.time() - csv_start:.2f} seconds")
    else:
        logging.info("Skipping CSV output (--skip-csv specified)")
    
    logging.info("Analysis complete")
    print(f"Climatology: {climatology:.2f}°C")
    print(f"Data coverage: {stats['data_coverage_pct']:.1f}%")
    print(f"Mean anomaly: {stats['mean_anomaly']:.3f}°C")
    print(f"Points >1°C anomaly: {stats['pct_above_1c']:.1f}%")

if __name__ == '__main__':
    main()
