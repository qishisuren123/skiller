#!/usr/bin/env python3
"""
Satellite brightness temperature data preprocessing CLI tool.
Converts NetCDF swath data to gridded CSV format with quality control.
"""

import argparse
import numpy as np
import pandas as pd
from netCDF4 import Dataset
import sys

def load_netcdf_data(filepath):
    """Load required variables from NetCDF file."""
    try:
        with Dataset(filepath, 'r') as nc:
            brightness_temp = nc.variables['brightness_temp'][:]
            latitude = nc.variables['latitude'][:]
            longitude = nc.variables['longitude'][:]
            quality_flag = nc.variables['quality_flag'][:]
            
        return brightness_temp, latitude, longitude, quality_flag
    except Exception as e:
        print(f"Error loading NetCDF file: {e}")
        sys.exit(1)

def apply_quality_control(brightness_temp, latitude, longitude, quality_flag):
    """Apply quality control mask and return valid data."""
    # Create mask for good quality data (quality_flag < 2)
    quality_mask = quality_flag < 2
    
    # Also mask invalid brightness temperature values
    valid_bt_mask = np.isfinite(brightness_temp)
    
    # Combine masks
    valid_mask = quality_mask & valid_bt_mask
    
    # Flatten arrays and apply mask
    valid_bt = brightness_temp[valid_mask].flatten()
    valid_lat = latitude[valid_mask].flatten()
    valid_lon = longitude[valid_mask].flatten()
    
    return valid_bt, valid_lat, valid_lon, valid_mask

def create_regular_grid(valid_lat, valid_lon, resolution):
    """Create regular lat/lon grid based on data extent."""
    lat_min, lat_max = np.min(valid_lat), np.max(valid_lat)
    lon_min, lon_max = np.min(valid_lon), np.max(valid_lon)
    
    # Extend bounds slightly to ensure all data is included
    lat_min = np.floor(lat_min / resolution) * resolution
    lat_max = np.ceil(lat_max / resolution) * resolution
    lon_min = np.floor(lon_min / resolution) * resolution
    lon_max = np.ceil(lon_max / resolution) * resolution
    
    lat_bins = np.arange(lat_min, lat_max + resolution, resolution)
    lon_bins = np.arange(lon_min, lon_max + resolution, resolution)
    
    return lat_bins, lon_bins

def regrid_data(valid_bt, valid_lat, valid_lon, lat_bins, lon_bins):
    """Regrid swath data onto regular grid with statistical aggregation."""
    # Assign each pixel to grid cell
    lat_idx = np.digitize(valid_lat, lat_bins) - 1
    lon_idx = np.digitize(valid_lon, lon_bins) - 1
    
    # Ensure indices are within bounds
    lat_idx = np.clip(lat_idx, 0, len(lat_bins) - 2)
    lon_idx = np.clip(lon_idx, 0, len(lon_bins) - 2)
    
    results = []
    
    # Process each grid cell
    for i in range(len(lat_bins) - 1):
        for j in range(len(lon_bins) - 1):
            # Find pixels in this grid cell
            cell_mask = (lat_idx == i) & (lon_idx == j)
            
            if np.any(cell_mask):
                # Calculate statistics for this cell
                cell_bt = valid_bt[cell_mask]
                mean_bt = np.mean(cell_bt)
                n_valid = len(cell_bt)
                
                # Grid cell center coordinates
                lat_center = (lat_bins[i] + lat_bins[i + 1]) / 2
                lon_center = (lon_bins[j] + lon_bins[j + 1]) / 2
                
                results.append({
                    'lat': lat_center,
                    'lon': lon_center,
                    'mean_bt': mean_bt,
                    'n_valid_pixels': n_valid
                })
    
    return results

def main():
    parser = argparse.ArgumentParser(
        description='Preprocess satellite brightness temperature data from NetCDF to gridded CSV'
    )
    parser.add_argument('--input', required=True, help='Input NetCDF file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--resolution', type=float, default=0.25, 
                       help='Grid resolution in degrees (default: 0.25)')
    
    args = parser.parse_args()
    
    # Validate resolution
    if args.resolution <= 0:
        print("Error: Resolution must be positive")
        sys.exit(1)
    
    print(f"Loading data from {args.input}...")
    brightness_temp, latitude, longitude, quality_flag = load_netcdf_data(args.input)
    
    total_pixels = brightness_temp.size
    print(f"Total pixels in dataset: {total_pixels}")
    
    print("Applying quality control...")
    valid_bt, valid_lat, valid_lon, valid_mask = apply_quality_control(
        brightness_temp, latitude, longitude, quality_flag
    )
    
    valid_pixels = len(valid_bt)
    print(f"Valid pixels after quality control: {valid_pixels}")
    
    if valid_pixels == 0:
        print("Error: No valid pixels found after quality control")
        sys.exit(1)
    
    print(f"Creating regular grid with {args.resolution}° resolution...")
    lat_bins, lon_bins = create_regular_grid(valid_lat, valid_lon, args.resolution)
    
    grid_dims = (len(lat_bins) - 1, len(lon_bins) - 1)
    print(f"Grid dimensions: {grid_dims[0]} x {grid_dims[1]} cells")
    
    print("Regridding data...")
    results = regrid_data(valid_bt, valid_lat, valid_lon, lat_bins, lon_bins)
    
    if not results:
        print("Error: No data in output grid")
        sys.exit(1)
    
    print(f"Populated grid cells: {len(results)}")
    
    # Convert to DataFrame and save
    df = pd.DataFrame(results)
    df.to_csv(args.output, index=False, float_format='%.6f')
    
    print(f"Results saved to {args.output}")
    print("\nProcessing Summary:")
    print(f"  Total pixels: {total_pixels}")
    print(f"  Valid pixels: {valid_pixels} ({100*valid_pixels/total_pixels:.1f}%)")
    print(f"  Grid dimensions: {grid_dims[0]} x {grid_dims[1]}")
    print(f"  Populated cells: {len(results)}")
    print(f"  Mean brightness temperature: {df['mean_bt'].mean():.2f} K")

if __name__ == '__main__':
    main()
