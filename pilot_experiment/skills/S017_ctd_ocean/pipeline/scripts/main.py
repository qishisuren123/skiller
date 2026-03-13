#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy.interpolate import interp1d

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle numpy types and NaN values"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            if np.isnan(obj):
                return None
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process CTD oceanographic profile data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--depth-resolution', type=float, default=1.0, 
                       help='Depth grid resolution in meters (default: 1.0)')
    return parser.parse_args()

def compute_sigma_t(salinity, temperature):
    """Compute potential density using simplified UNESCO equation"""
    sigma_t = (-0.093 + 0.808*salinity - 0.0016*salinity**2 + 
               (-0.0069 + 0.0025*salinity)*temperature - 0.0001*temperature**2)
    return sigma_t

def find_thermocline_depth(depth, temperature):
    """Find thermocline depth (depth of maximum negative dT/dz)"""
    # Check if we have enough valid data points
    valid_mask = ~np.isnan(temperature)
    valid_count = np.sum(valid_mask)
    
    if valid_count < 3:  # Need at least 3 points for meaningful gradient
        return np.nan
    
    valid_depth = depth[valid_mask]
    valid_temp = temperature[valid_mask]
    
    # Check for constant temperature (no thermocline)
    temp_range = np.max(valid_temp) - np.min(valid_temp)
    if temp_range < 0.1:  # Less than 0.1°C variation
        return np.nan
    
    dt_dz = np.gradient(valid_temp, valid_depth)
    
    # Check if all gradients are very small (essentially flat profile)
    if np.max(np.abs(dt_dz)) < 0.01:  # Less than 0.01°C/m gradient
        return np.nan
    
    thermocline_idx = np.argmin(dt_dz)
    return valid_depth[thermocline_idx]

def find_mixed_layer_depth(depth, temperature):
    """Find mixed layer depth (T differs from surface by > 0.5°C)"""
    # Check if we have valid data
    valid_mask = ~np.isnan(temperature)
    valid_count = np.sum(valid_mask)
    
    if valid_count < 2:  # Need at least 2 points
        return np.nan
    
    valid_depth = depth[valid_mask]
    valid_temp = temperature[valid_mask]
    
    surface_temp = valid_temp[0]  # Shallowest measurement
    
    # Check for constant temperature profile
    temp_range = np.max(valid_temp) - np.min(valid_temp)
    if temp_range < 0.5:  # If total variation is less than our threshold
        return valid_depth[-1]  # Return max depth (no mixed layer boundary)
    
    temp_diff = np.abs(valid_temp - surface_temp)
    
    # Find first point where difference > 0.5°C
    mixed_layer_idx = np.where(temp_diff > 0.5)[0]
    if len(mixed_layer_idx) > 0:
        return valid_depth[mixed_layer_idx[0]]
    
    # If no mixed layer found, return the deepest measurement
    return valid_depth[-1]

def process_station_standardized(station_data, standard_depth_grid):
    """Process a single station's data using standardized depth grid"""
    # Sort by depth
    station_data = station_data.sort_values('depth_m')
    
    station_min_depth = station_data['depth_m'].min()
    station_max_depth = station_data['depth_m'].max()
    
    # Check for minimal data
    if len(station_data) < 2:
        print(f"Warning: Station has only {len(station_data)} data point(s) - skipping analysis")
        # Return arrays filled with NaN
        return {
            'temperature': np.full_like(standard_depth_grid, np.nan),
            'salinity': np.full_like(standard_depth_grid, np.nan),
            'dissolved_oxygen': np.full_like(standard_depth_grid, np.nan),
            'sigma_t': np.full_like(standard_depth_grid, np.nan),
            'thermocline_depth': np.nan,
            'mixed_layer_depth': np.nan,
            'station_max_depth': station_max_depth,
            'station_min_depth': station_min_depth
        }
    
    # Interpolate to standardized grid
    interp_temp = interp1d(station_data['depth_m'], station_data['temperature_C'], 
                          kind='linear', bounds_error=False, fill_value=np.nan)
    interp_sal = interp1d(station_data['depth_m'], station_data['salinity_PSU'], 
                         kind='linear', bounds_error=False, fill_value=np.nan)
    interp_do = interp1d(station_data['depth_m'], station_data['dissolved_oxygen_mL_L'], 
                        kind='linear', bounds_error=False, fill_value=np.nan)
    
    temp_interp = interp_temp(standard_depth_grid)
    sal_interp = interp_sal(standard_depth_grid)
    do_interp = interp_do(standard_depth_grid)
    
    # Compute sigma-t (will have NaN where data is missing)
    sigma_t = compute_sigma_t(sal_interp, temp_interp)
    
    # For analysis, use only the valid depth range for this station
    valid_mask = (standard_depth_grid >= station_min_depth) & (standard_depth_grid <= station_max_depth)
    valid_depths = standard_depth_grid[valid_mask]
    valid_temps = temp_interp[valid_mask]
    
    # Find thermocline and mixed layer depths using valid data only
    thermocline_depth = find_thermocline_depth(valid_depths, valid_temps)
    mixed_layer_depth = find_mixed_layer_depth(valid_depths, valid_temps)
    
    return {
        'temperature': temp_interp,
        'salinity': sal_interp,
        'dissolved_oxygen': do_interp,
        'sigma_t': sigma_t,
        'thermocline_depth': thermocline_depth,
        'mixed_layer_depth': mixed_layer_depth,
        'station_max_depth': station_max_depth,
        'station_min_depth': station_min_depth
    }

def main():
    args = parse_arguments()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Read input data
    df = pd.read_csv(args.input)
    print(f"Loaded data with {len(df)} records")
    
    # Find global depth range across all stations
    global_min_depth = df['depth_m'].min()
    global_max_depth = df['depth_m'].max()
    
    # Create standardized depth grid
    grid_start = np.floor(global_min_depth / args.depth_resolution) * args.depth_resolution
    grid_end = np.ceil(global_max_depth / args.depth_resolution) * args.depth_resolution
    standard_depth_grid = np.arange(grid_start, grid_end + args.depth_resolution, args.depth_resolution)
    
    print(f"Using standardized depth grid: {grid_start:.1f} to {grid_end:.1f} m")
    
    # Process each station
    stations = df['station_id'].unique()
    print(f"Processing {len(stations)} stations")
    
    all_profiles = []
    station_summaries = {}
    thermocline_depths = []
    
    for station_id in stations:
        station_data = df[df['station_id'] == station_id]
        result = process_station_standardized(station_data, standard_depth_grid)
        
        # Store profile data
        for i, depth in enumerate(standard_depth_grid):
            all_profiles.append({
                'station_id': station_id,
                'depth_m': depth,
                'temperature_C': result['temperature'][i],
                'salinity_PSU': result['salinity'][i],
                'dissolved_oxygen_mL_L': result['dissolved_oxygen'][i],
                'sigma_t': result['sigma_t'][i]
            })
        
        # Store station summary
        station_summaries[station_id] = {
            'thermocline_depth': result['thermocline_depth'],
            'mixed_layer_depth': result['mixed_layer_depth'],
            'max_depth': result['station_max_depth'],
            'min_depth': result['station_min_depth']
        }
        
        thermocline_depths.append(result['thermocline_depth'])
    
    # Save outputs
    profiles_df = pd.DataFrame(all_profiles)
    profiles_df.to_csv(os.path.join(args.output, 'interpolated_profiles.csv'), index=False)
    
    # Use custom encoder for JSON serialization
    with open(os.path.join(args.output, 'station_summary.json'), 'w') as f:
        json.dump(station_summaries, f, indent=2, cls=NumpyEncoder)
    
    # Filter out NaN values for statistics
    valid_thermocline_depths = [d for d in thermocline_depths if not np.isnan(d)]
    
    # Print summary statistics
    depth_range = (global_min_depth, global_max_depth)
    if valid_thermocline_depths:
        mean_thermocline = np.mean(valid_thermocline_depths)
        print(f"Mean thermocline depth: {mean_thermocline:.1f} m ({len(valid_thermocline_depths)}/{len(stations)} stations)")
    else:
        print("No valid thermocline depths found")
    
    print(f"Number of stations: {len(stations)}")
    print(f"Depth range: {depth_range[0]:.1f} - {depth_range[1]:.1f} m")

if __name__ == "__main__":
    main()
