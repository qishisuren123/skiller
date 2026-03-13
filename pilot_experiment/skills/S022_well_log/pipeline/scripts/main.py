#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy.interpolate import interp1d

def classify_lithology(vsh, phit, resistivity, bulk_density, neutron_porosity):
    """Classify lithology based on crossplot rules - vectorized version with proper priority"""
    # Initialize with default
    lithology = np.full(len(vsh), 'siltstone', dtype=object)
    
    # Apply rules in priority order - most specific first
    # Rule 1: Shale (highest priority - clear definition)
    shale_mask = vsh >= 0.6
    
    # Rule 2: Limestone (should be checked before sandstone)
    limestone_mask = (bulk_density > 2.5) & (neutron_porosity < 0.15) & (vsh < 0.3)
    
    # Rule 3: Sandstone (checked after limestone to avoid conflicts)
    sandstone_mask = (vsh < 0.3) & (phit > 0.1) & (resistivity > 10) & (~limestone_mask)
    
    # Apply classifications
    lithology[limestone_mask] = 'limestone'  # Apply limestone first
    lithology[sandstone_mask] = 'sandstone'  # Then sandstone (excluding limestone)
    lithology[shale_mask] = 'shale'          # Shale overrides others
    
    return lithology

def main():
    parser = argparse.ArgumentParser(description='Resample well log data and classify lithology')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--depth-step', type=float, default=0.5, help='Depth step in meters')
    
    args = parser.parse_args()
    
    # Read input data and sort by depth
    df = pd.read_csv(args.input)
    df = df.sort_values('depth').reset_index(drop=True)
    print(f"Loaded {len(df)} data points")
    
    # Check for data quality issues
    print(f"Bulk density range: {df['bulk_density'].min():.2f} to {df['bulk_density'].max():.2f} g/cm3")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Define new uniform depth grid
    depth_min, depth_max = df['depth'].min(), df['depth'].max()
    new_depths = np.arange(depth_min, depth_max + args.depth_step/2, args.depth_step)
    new_depths = new_depths[new_depths <= depth_max]
    
    # Resample all log curves
    resampled_data = {'depth': new_depths}
    log_columns = ['gamma_ray', 'resistivity', 'neutron_porosity', 'bulk_density', 'caliper']
    
    for col in log_columns:
        interpolator = interp1d(df['depth'], df[col], kind='linear', 
                               bounds_error=False, fill_value=(df[col].iloc[0], df[col].iloc[-1]))
        resampled_data[col] = interpolator(new_depths)
    
    resampled_df = pd.DataFrame(resampled_data)
    
    # Compute PHIT with proper bounds checking
    matrix_density = 2.65
    fluid_density = 1.0
    
    raw_phit = (matrix_density - resampled_df['bulk_density']) / (matrix_density - fluid_density)
    resampled_df['PHIT'] = np.clip(raw_phit, 0.0, 0.5)
    
    # Check for problematic values
    negative_phit = (raw_phit < 0).sum()
    high_phit = (raw_phit > 0.5).sum()
    if negative_phit > 0:
        print(f"Warning: {negative_phit} samples had negative porosity (clipped to 0)")
    if high_phit > 0:
        print(f"Warning: {high_phit} samples had porosity > 50% (clipped to 0.5)")
    
    # Compute Vsh
    gr_min, gr_max = df['gamma_ray'].min(), df['gamma_ray'].max()
    if gr_max == gr_min:
        print("Warning: Gamma ray values are constant, setting Vsh to 0")
        resampled_df['Vsh'] = 0.0
    else:
        resampled_df['Vsh'] = np.clip((resampled_df['gamma_ray'] - gr_min) / (gr_max - gr_min), 0, 1)
    
    print(f"PHIT range after clipping: {resampled_df['PHIT'].min():.3f} to {resampled_df['PHIT'].max():.3f}")
    
    # Classify lithology using vectorized function
    resampled_df['lithology'] = classify_lithology(
        resampled_df['Vsh'], 
        resampled_df['PHIT'], 
        resampled_df['resistivity'],
        resampled_df['bulk_density'], 
        resampled_df['neutron_porosity']
    )
    
    # Save outputs
    resampled_df.to_csv(os.path.join(args.output, 'resampled_log.csv'), index=False)
    
    litho_df = resampled_df[['depth', 'lithology']]
    litho_df.to_csv(os.path.join(args.output, 'lithology_classification.csv'), index=False)
    
    # Generate summary
    layer_counts = resampled_df['lithology'].value_counts().to_dict()
    summary = {
        'total_depth_range': float(depth_max - depth_min),
        'n_samples': len(resampled_df),
        'layer_counts': layer_counts,
        'mean_porosity': float(resampled_df['PHIT'].mean()),
        'mean_Vsh': float(resampled_df['Vsh'].mean())
    }
    
    with open(os.path.join(args.output, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print results
    print(f"Depth range: {depth_min:.1f}m to {depth_max:.1f}m ({summary['total_depth_range']:.1f}m total)")
    print(f"Resampled to {len(resampled_df)} points")
    print("Lithology distribution:")
    for litho, count in layer_counts.items():
        print(f"  {litho}: {count}")

if __name__ == '__main__':
    main()
