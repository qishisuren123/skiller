#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import xarray as xr
import logging
from pathlib import Path

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Preprocess satellite brightness temperature data')
    parser.add_argument('--input', required=True, help='Input NetCDF file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--resolution', type=float, default=0.25, 
                       help='Grid resolution in degrees (default: 0.25)')
    return parser.parse_args()

def load_satellite_data(input_file):
    """Load satellite data from NetCDF file"""
    logging.info(f"Loading data from {input_file}")
    ds = xr.open_dataset(input_file)
    
    brightness_temp = ds['brightness_temp'].values
    latitude = ds['latitude'].values
    longitude = ds['longitude'].values
    quality_flag = ds['quality_flag'].values
    
    ds.close()
    return brightness_temp, latitude, longitude, quality_flag

def mask_bad_data(brightness_temp, quality_flag):
    """Mask pixels with quality_flag >= 2"""
    mask = quality_flag >= 2
    brightness_temp_masked = brightness_temp.copy()
    brightness_temp_masked[mask] = np.nan
    return brightness_temp_masked

def detect_dateline_crossing(lon_valid):
    """Detect if data crosses the dateline and adjust if needed"""
    lon_range = np.max(lon_valid) - np.min(lon_valid)
    
    if lon_range > 180:  # Likely crosses dateline
        logging.info("Detected dateline crossing, adjusting longitudes")
        # Convert to 0-360 range to avoid the discontinuity
        lon_adjusted = np.where(lon_valid < 0, lon_valid + 360, lon_valid)
        return lon_adjusted, True
    else:
        return lon_valid, False

def regrid_data(brightness_temp, latitude, longitude, resolution):
    """Regrid swath data to regular lat/lon grid using vectorized operations"""
    # Flatten arrays for easier processing
    bt_flat = brightness_temp.flatten()
    lat_flat = latitude.flatten()
    lon_flat = longitude.flatten()
    
    # Remove invalid data
    valid_mask = ~(np.isnan(lat_flat) | np.isnan(lon_flat) | np.isnan(bt_flat))
    bt_valid = bt_flat[valid_mask]
    lat_valid = lat_flat[valid_mask]
    lon_valid = lon_flat[valid_mask]
    
    if len(lat_valid) == 0:
        logging.warning("No valid data found after quality filtering")
        return np.array([]), np.array([]), np.array([]).reshape(0, 0), np.array([]).reshape(0, 0)
    
    logging.info(f"Processing {len(bt_valid):,} valid pixels")
    
    # Handle dateline crossing
    lon_for_grid, crosses_dateline = detect_dateline_crossing(lon_valid)
    
    # Define grid bounds
    lat_min = np.floor(np.min(lat_valid) / resolution) * resolution
    lat_max = np.ceil(np.max(lat_valid) / resolution) * resolution
    lon_min = np.floor(np.min(lon_for_grid) / resolution) * resolution  
    lon_max = np.ceil(np.max(lon_for_grid) / resolution) * resolution
    
    # Create regular grid
    lat_grid = np.arange(lat_min, lat_max + resolution, resolution)
    lon_grid = np.arange(lon_min, lon_max + resolution, resolution)
    
    # Convert back to -180/180 range for output if needed
    if crosses_dateline:
        lon_grid_output = np.where(lon_grid > 180, lon_grid - 360, lon_grid)
        logging.info(f"Grid bounds: lat [{lat_min:.2f}, {lat_max:.2f}], lon [{np.min(lon_grid_output):.2f}, {np.max(lon_grid_output):.2f}] (crosses dateline)")
    else:
        lon_grid_output = lon_grid
        logging.info(f"Grid bounds: lat [{lat_min:.2f}, {lat_max:.2f}], lon [{lon_min:.2f}, {lon_max:.2f}]")
    
    logging.info(f"Grid dimensions: {len(lat_grid)} x {len(lon_grid)}")
    
    # Convert coordinates to grid indices
    lat_indices = ((lat_valid - lat_min) / resolution).astype(int)
    lon_indices = ((lon_for_grid - lon_min) / resolution).astype(int)
    
    # Clip indices to valid range
    lat_indices = np.clip(lat_indices, 0, len(lat_grid) - 1)
    lon_indices = np.clip(lon_indices, 0, len(lon_grid) - 1)
    
    # Initialize output arrays
    mean_bt = np.full((len(lat_grid), len(lon_grid)), np.nan)
    n_valid = np.zeros((len(lat_grid), len(lon_grid)), dtype=int)
    
    # Use numpy.bincount for efficient aggregation
    logging.info("Aggregating data to grid...")
    
    # Convert 2D indices to 1D for bincount
    linear_indices = lat_indices * len(lon_grid) + lon_indices
    max_index = len(lat_grid) * len(lon_grid)
    
    # Sum brightness temperatures for each grid cell
    bt_sums = np.bincount(linear_indices, weights=bt_valid, minlength=max_index)
    counts = np.bincount(linear_indices, minlength=max_index)
    
    # Reshape back to 2D
    bt_sums_2d = bt_sums.reshape(len(lat_grid), len(lon_grid))
    counts_2d = counts.reshape(len(lat_grid), len(lon_grid))
    
    # Calculate means where we have data
    valid_cells = counts_2d > 0
    mean_bt[valid_cells] = bt_sums_2d[valid_cells] / counts_2d[valid_cells]
    n_valid = counts_2d.astype(int)
    
    return lat_grid, lon_grid_output, mean_bt, n_valid

def save_results(lat_grid, lon_grid, mean_bt, n_valid, output_file):
    """Save results to CSV file"""
    logging.info(f"Saving results to {output_file}")
    
    # Handle empty case
    if len(lat_grid) == 0:
        logging.warning("No data to save - creating empty CSV with headers")
        df = pd.DataFrame(columns=['lat', 'lon', 'mean_bt', 'n_valid_pixels'])
        df.to_csv(output_file, index=False)
        return
    
    # Create output data
    results = []
    for i, lat in enumerate(lat_grid):
        for j, lon in enumerate(lon_grid):
            if not np.isnan(mean_bt[i, j]):
                results.append({
                    'lat': lat,
                    'lon': lon, 
                    'mean_bt': mean_bt[i, j],
                    'n_valid_pixels': n_valid[i, j]
                })
    
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    logging.info(f"Saved {len(df)} grid cells to CSV")

def print_summary(brightness_temp, quality_flag, lat_grid, lon_grid, n_valid):
    """Print processing summary"""
    total_pixels = brightness_temp.size
    valid_pixels = np.sum(quality_flag < 2)
    
    if len(lat_grid) == 0:
        grid_cells_with_data = 0
        grid_dims = "0 x 0"
    else:
        grid_cells_with_data = np.sum(n_valid > 0)
        grid_dims = f"{len(lat_grid)} x {len(lon_grid)}"
    
    print("\n=== PROCESSING SUMMARY ===")
    print(f"Total pixels: {total_pixels:,}")
    print(f"Valid pixels (quality_flag < 2): {valid_pixels:,}")
    print(f"Grid dimensions: {grid_dims}")
    print(f"Grid cells with data: {grid_cells_with_data:,}")

def main():
    setup_logging()
    args = parse_arguments()
    
    # Load data
    brightness_temp, latitude, longitude, quality_flag = load_satellite_data(args.input)
    
    # Mask bad data
    brightness_temp_masked = mask_bad_data(brightness_temp, quality_flag)
    
    # Regrid data
    lat_grid, lon_grid, mean_bt, n_valid = regrid_data(
        brightness_temp_masked, latitude, longitude, args.resolution)
    
    # Save results
    save_results(lat_grid, lon_grid, mean_bt, n_valid, args.output)
    
    # Print summary
    print_summary(brightness_temp, quality_flag, lat_grid, lon_grid, n_valid)
    
    logging.info("Processing complete")

if __name__ == "__main__":
    main()
