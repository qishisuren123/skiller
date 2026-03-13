import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy.interpolate import interp1d

def calculate_sigma_t(salinity, temperature):
    """Calculate potential density using simplified UNESCO equation"""
    S, T = salinity, temperature
    sigma_t = (-0.093 + 0.808*S - 0.0016*S**2 + 
               (-0.0069 + 0.0025*S)*T - 0.0001*T**2)
    return sigma_t

def find_thermocline_depth(depth, temperature):
    """Find thermocline depth as maximum temperature gradient"""
    if len(depth) < 3:
        return np.nan
    
    dt_dz = np.gradient(temperature, depth)
    # Find maximum absolute gradient, excluding boundaries
    valid_idx = ~np.isnan(dt_dz[1:-1])
    if not np.any(valid_idx):
        return np.nan
    
    max_grad_idx = np.nanargmax(np.abs(dt_dz[1:-1])) + 1
    return depth[max_grad_idx]

def find_mixed_layer_depth(depth, temperature, threshold=0.5):
    """Find mixed layer depth where temperature differs from surface by threshold"""
    if len(temperature) < 2:
        return np.nan
    
    surface_temp = temperature[0]  # Use shallowest measurement
    temp_diff = np.abs(temperature - surface_temp)
    
    # Find first depth where difference exceeds threshold
    exceed_idx = np.where(temp_diff > threshold)[0]
    if len(exceed_idx) == 0:
        return depth[-1]  # Mixed layer extends to bottom
    
    return depth[exceed_idx[0]]

def process_station(station_data, depth_resolution):
    """Process a single CTD station"""
    # Sort by depth and remove duplicates
    station_data = station_data.sort_values('depth_m').drop_duplicates('depth_m')
    
    if len(station_data) < 3:
        return None, None
    
    depths = station_data['depth_m'].values
    max_depth = depths.max()
    
    # Create regular depth grid
    depth_grid = np.arange(0, max_depth + depth_resolution, depth_resolution)
    
    # Interpolate all variables
    interpolated_data = {'depth_m': depth_grid}
    
    for col in ['temperature_C', 'salinity_PSU', 'dissolved_oxygen_mL_L']:
        if col in station_data.columns:
            # Remove NaN values for interpolation
            valid_mask = ~station_data[col].isna()
            if valid_mask.sum() >= 2:  # Need at least 2 points
                f_interp = interp1d(depths[valid_mask], 
                                  station_data[col].values[valid_mask],
                                  kind='linear', bounds_error=False, 
                                  fill_value=np.nan)
                interpolated_data[col] = f_interp(depth_grid)
            else:
                interpolated_data[col] = np.full(len(depth_grid), np.nan)
    
    # Calculate sigma-t if we have temperature and salinity
    if 'temperature_C' in interpolated_data and 'salinity_PSU' in interpolated_data:
        interpolated_data['sigma_t'] = calculate_sigma_t(
            interpolated_data['salinity_PSU'], 
            interpolated_data['temperature_C']
        )
    
    # Calculate oceanographic features
    temp_interp = interpolated_data.get('temperature_C', np.full(len(depth_grid), np.nan))
    
    thermocline_depth = find_thermocline_depth(depth_grid, temp_interp)
    mixed_layer_depth = find_mixed_layer_depth(depth_grid, temp_interp)
    
    # Create summary
    summary = {
        'max_depth': float(max_depth),
        'thermocline_depth': float(thermocline_depth) if not np.isnan(thermocline_depth) else None,
        'mixed_layer_depth': float(mixed_layer_depth) if not np.isnan(mixed_layer_depth) else None,
        'surface_temperature': float(temp_interp[0]) if not np.isnan(temp_interp[0]) else None,
        'bottom_temperature': float(temp_interp[-1]) if not np.isnan(temp_interp[-1]) else None
    }
    
    return interpolated_data, summary

def main():
    parser = argparse.ArgumentParser(description='Process CTD oceanographic profile data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--depth-resolution', type=float, default=1.0, 
                       help='Depth resolution in meters (default: 1.0)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input):
        raise FileNotFoundError(f"Input file not found: {args.input}")
    
    if args.depth_resolution <= 0:
        raise ValueError("Depth resolution must be positive")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    print(f"Loading CTD data from {args.input}")
    data = pd.read_csv(args.input)
    
    # Validate required columns
    required_cols = ['station_id', 'depth_m', 'temperature_C', 'salinity_PSU', 'dissolved_oxygen_mL_L']
    missing_cols = [col for col in required_cols if col not in data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Process each station
    all_interpolated = []
    station_summaries = {}
    thermocline_depths = []
    
    stations = data['station_id'].unique()
    print(f"Processing {len(stations)} stations...")
    
    for station_id in stations:
        station_data = data[data['station_id'] == station_id].copy()
        
        try:
            interpolated_data, summary = process_station(station_data, args.depth_resolution)
            
            if interpolated_data is not None:
                # Add station_id to interpolated data
                interp_df = pd.DataFrame(interpolated_data)
                interp_df['station_id'] = station_id
                all_interpolated.append(interp_df)
                
                station_summaries[str(station_id)] = summary
                
                if summary['thermocline_depth'] is not None:
                    thermocline_depths.append(summary['thermocline_depth'])
            else:
                print(f"Warning: Skipping station {station_id} - insufficient data")
                
        except Exception as e:
            print(f"Warning: Error processing station {station_id}: {e}")
            continue
    
    # Combine all interpolated data
    if all_interpolated:
        combined_profiles = pd.concat(all_interpolated, ignore_index=True)
        
        # Reorder columns
        col_order = ['station_id', 'depth_m', 'temperature_C', 'salinity_PSU', 
                    'dissolved_oxygen_mL_L', 'sigma_t']
        combined_profiles = combined_profiles[[col for col in col_order if col in combined_profiles.columns]]
        
        # Save outputs
        output_csv = os.path.join(args.output, 'interpolated_profiles.csv')
        combined_profiles.to_csv(output_csv, index=False)
        print(f"Saved interpolated profiles to {output_csv}")
        
        output_json = os.path.join(args.output, 'station_summary.json')
        with open(output_json, 'w') as f:
            json.dump(station_summaries, f, indent=2)
        print(f"Saved station summaries to {output_json}")
        
        # Print summary statistics
        depth_range = (combined_profiles['depth_m'].min(), combined_profiles['depth_m'].max())
        mean_thermocline = np.mean(thermocline_depths) if thermocline_depths else None
        
        print(f"\nProcessing Summary:")
        print(f"Number of stations processed: {len(station_summaries)}")
        print(f"Depth range: {depth_range[0]:.1f} - {depth_range[1]:.1f} m")
        if mean_thermocline is not None:
            print(f"Mean thermocline depth: {mean_thermocline:.1f} m")
        else:
            print("Mean thermocline depth: Not available")
    else:
        print("No stations were successfully processed")

if __name__ == "__main__":
    main()
