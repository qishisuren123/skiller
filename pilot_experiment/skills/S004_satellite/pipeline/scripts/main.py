#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import xarray as xr
from collections import defaultdict

def handle_longitude_wraparound(lon_flat):
    """Handle longitude wraparound at 180°/-180°"""
    lon_range = lon_flat.max() - lon_flat.min()
    
    # If longitude range > 180°, likely crossing dateline
    if lon_range > 180:
        print("Detected longitude wraparound - converting to 0-360° system")
        # Convert negative longitudes to 0-360 system
        lon_flat = np.where(lon_flat < 0, lon_flat + 360, lon_flat)
        wraparound = True
    else:
        wraparound = False
    
    return lon_flat, wraparound

def convert_longitude_back(lon_centers, wraparound):
    """Convert longitude back to -180 to 180 if needed"""
    if wraparound:
        # Convert back to -180 to 180 system for output
        lon_centers = np.where(lon_centers > 180, lon_centers - 360, lon_centers)
    return lon_centers

def preprocess_satellite_data(input_file, output_file, resolution=0.25, min_pixels=5, remove_outliers=True):
    # Load NetCDF data
    ds = xr.open_dataset(input_file)
    
    # Extract variables
    bt = ds['brightness_temp'].values
    lat = ds['latitude'].values
    lon = ds['longitude'].values
    qf = ds['quality_flag'].values
    
    # Mask bad quality data
    valid_mask = qf < 2
    
    # Flatten arrays and keep only valid pixels
    bt_flat = bt[valid_mask]
    lat_flat = lat[valid_mask]
    lon_flat = lon[valid_mask]
    
    # Handle longitude wraparound
    lon_flat, wraparound = handle_longitude_wraparound(lon_flat)
    
    # Remove outliers if requested
    if remove_outliers:
        q1, q3 = np.percentile(bt_flat, [25, 75])
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outlier_mask = (bt_flat >= lower_bound) & (bt_flat <= upper_bound)
        bt_flat = bt_flat[outlier_mask]
        lat_flat = lat_flat[outlier_mask]
        lon_flat = lon_flat[outlier_mask]
        
        print(f"Removed {np.sum(~outlier_mask)} outliers (BT < {lower_bound:.1f} or > {upper_bound:.1f})")
    
    # Create regular grid - align grid to resolution boundaries
    lat_min, lat_max = lat_flat.min(), lat_flat.max()
    lon_min, lon_max = lon_flat.min(), lon_flat.max()
    
    # Align grid boundaries to resolution
    lat_start = np.floor(lat_min / resolution) * resolution
    lat_end = np.ceil(lat_max / resolution) * resolution
    lon_start = np.floor(lon_min / resolution) * resolution  
    lon_end = np.ceil(lon_max / resolution) * resolution
    
    # Create grid cell centers
    lat_centers = np.arange(lat_start + resolution/2, lat_end, resolution)
    lon_centers = np.arange(lon_start + resolution/2, lon_end, resolution)
    
    # Convert pixel coordinates to grid indices
    lat_indices = np.floor((lat_flat - lat_start) / resolution).astype(int)
    lon_indices = np.floor((lon_flat - lon_start) / resolution).astype(int)
    
    # Remove out-of-bounds indices
    valid_indices = ((lat_indices >= 0) & (lat_indices < len(lat_centers)) & 
                    (lon_indices >= 0) & (lon_indices < len(lon_centers)))
    
    lat_indices = lat_indices[valid_indices]
    lon_indices = lon_indices[valid_indices]
    bt_valid = bt_flat[valid_indices]
    
    # Group pixels by grid cell
    grid_data = defaultdict(list)
    for lat_idx, lon_idx, bt_val in zip(lat_indices, lon_indices, bt_valid):
        grid_data[(lat_idx, lon_idx)].append(bt_val)
    
    # Calculate statistics for each grid cell with minimum pixel filter
    results = []
    filtered_cells = 0
    
    for (lat_idx, lon_idx), bt_values in grid_data.items():
        if len(bt_values) >= min_pixels:
            grid_lat = lat_centers[lat_idx]
            grid_lon = lon_centers[lon_idx]
            
            # Convert longitude back if needed
            if wraparound and grid_lon > 180:
                grid_lon -= 360
            
            results.append({
                'lat': grid_lat,
                'lon': grid_lon,
                'mean_bt': np.mean(bt_values),
                'n_valid_pixels': len(bt_values)
            })
        else:
            filtered_cells += 1
    
    df = pd.DataFrame(results)
    df.to_csv(output_file, index=False)
    
    # Print summary
    total_pixels = bt.size
    valid_pixels = np.sum(valid_mask)
    final_pixels = len(bt_valid)
    
    print(f"Total pixels: {total_pixels}")
    print(f"Valid pixels (quality filter): {valid_pixels}")
    print(f"Final pixels (after outlier removal): {final_pixels}")
    print(f"Grid dimensions: {len(lat_centers)} x {len(lon_centers)}")
    print(f"Grid cells with data: {len(grid_data)}")
    print(f"Grid cells filtered (< {min_pixels} pixels): {filtered_cells}")
    print(f"Output grid cells: {len(results)}")
    
    if len(results) > 0:
        print(f"BT range in output: {df['mean_bt'].min():.1f} to {df['mean_bt'].max():.1f}")
        print(f"Pixel count range: {df['n_valid_pixels'].min()} to {df['n_valid_pixels'].max()}")

def main():
    parser = argparse.ArgumentParser(description='Preprocess satellite brightness temperature data')
    parser.add_argument('--input', required=True, help='Input NetCDF file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--resolution', type=float, default=0.25, help='Grid resolution in degrees')
    parser.add_argument('--min-pixels', type=int, default=5, help='Minimum pixels per grid cell')
    parser.add_argument('--no-outlier-removal', action='store_true', help='Skip outlier removal')
    
    args = parser.parse_args()
    preprocess_satellite_data(args.input, args.output, args.resolution, 
                            args.min_pixels, not args.no_outlier_removal)

if __name__ == '__main__':
    main()
