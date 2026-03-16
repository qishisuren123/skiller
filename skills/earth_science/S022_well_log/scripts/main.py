#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy import interpolate
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    parser = argparse.ArgumentParser(description='Resample well log data and classify lithology')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--depth-step', type=float, default=0.5, help='Depth step for resampling (meters)')
    parser.add_argument('--matrix-density', type=float, default=None, help='Matrix density for porosity calculation (g/cm3)')
    return parser.parse_args()

def load_well_data(input_file):
    """Load well log data from CSV file"""
    df = pd.read_csv(input_file)
    required_columns = ['depth', 'gamma_ray', 'resistivity', 'neutron_porosity', 'bulk_density', 'caliper']
    
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    return df

def resample_logs(df, depth_step):
    """Resample all log curves to uniform depth intervals"""
    depth_min = df['depth'].min()
    depth_max = df['depth'].max()
    
    # Create uniform depth array
    uniform_depth = np.arange(depth_min, depth_max + depth_step, depth_step)
    
    # Initialize resampled dataframe
    resampled_df = pd.DataFrame({'depth': uniform_depth})
    
    # Interpolate each log curve
    log_columns = ['gamma_ray', 'resistivity', 'neutron_porosity', 'bulk_density', 'caliper']
    
    for col in log_columns:
        # Remove NaN values for interpolation
        valid_mask = ~np.isnan(df[col])
        if valid_mask.sum() < 2:
            logging.warning(f"Not enough valid data points for {col}")
            resampled_df[col] = np.nan
            continue
        
        # Use numpy interp instead of scipy for better compatibility
        resampled_df[col] = np.interp(
            uniform_depth,
            df['depth'][valid_mask], 
            df[col][valid_mask]
        )
    
    return resampled_df

def estimate_matrix_density(df):
    """Estimate appropriate matrix density from bulk density distribution"""
    
    # Use 95th percentile of bulk density as matrix density estimate
    # This assumes the tightest (lowest porosity) rocks represent near-matrix density
    matrix_density = np.percentile(df['bulk_density'].dropna(), 95)
    
    # Add a small buffer to ensure positive porosities
    matrix_density += 0.05
    
    logging.info(f"Estimated matrix density: {matrix_density:.2f} g/cm3 (95th percentile + 0.05)")
    
    return matrix_density

def compute_derived_logs(df, matrix_density=None):
    """Compute PHIT and Vsh from basic log measurements"""
    
    # Estimate matrix density if not provided
    if matrix_density is None:
        matrix_density = estimate_matrix_density(df)
    else:
        logging.info(f"Using specified matrix density: {matrix_density:.2f} g/cm3")
    
    # PHIT (total porosity) = (matrix_density - bulk_density) / (matrix_density - fluid_density)
    fluid_density = 1.0  # water
    df['PHIT'] = (matrix_density - df['bulk_density']) / (matrix_density - fluid_density)
    
    # Clip porosity to physically reasonable bounds [0, 0.5]
    df['PHIT'] = np.clip(df['PHIT'], 0.0, 0.5)
    
    # Debug: Check for NaN values
    nan_phit = df['PHIT'].isna().sum()
    if nan_phit > 0:
        logging.warning(f"Found {nan_phit} NaN values in PHIT calculation")
    
    # Vsh (shale volume) from gamma ray
    gr_min = df['gamma_ray'].min()
    gr_max = df['gamma_ray'].max()
    
    logging.info(f"Gamma ray range: {gr_min:.1f} - {gr_max:.1f} API")
    
    if gr_max > gr_min:
        df['Vsh'] = (df['gamma_ray'] - gr_min) / (gr_max - gr_min)
        df['Vsh'] = np.clip(df['Vsh'], 0, 1)
    else:
        logging.warning("Gamma ray has no variation, setting Vsh to 0")
        df['Vsh'] = 0.0
    
    # Debug: Check for NaN values
    nan_vsh = df['Vsh'].isna().sum()
    if nan_vsh > 0:
        logging.warning(f"Found {nan_vsh} NaN values in Vsh calculation")
    
    # Print some statistics for debugging
    logging.info(f"PHIT range: {df['PHIT'].min():.3f} - {df['PHIT'].max():.3f}")
    logging.info(f"Vsh range: {df['Vsh'].min():.3f} - {df['Vsh'].max():.3f}")
    logging.info(f"Bulk density range: {df['bulk_density'].min():.2f} - {df['bulk_density'].max():.2f}")
    logging.info(f"Resistivity range: {df['resistivity'].min():.1f} - {df['resistivity'].max():.1f}")
    
    return df

def classify_lithology(df):
    """Classify lithology based on crossplot rules"""
    lithology = []
    
    # Debug counters
    rule_counts = {'sandstone': 0, 'shale': 0, 'limestone': 0, 'siltstone': 0}
    
    for idx, row in df.iterrows():
        vsh = row['Vsh']
        phit = row['PHIT']
        resistivity = row['resistivity']
        bulk_density = row['bulk_density']
        neutron_porosity = row['neutron_porosity']
        
        # Check for NaN values that could affect classification
        if pd.isna(vsh) or pd.isna(phit) or pd.isna(resistivity) or pd.isna(bulk_density) or pd.isna(neutron_porosity):
            lithology.append('unknown')
            continue
        
        if vsh < 0.3 and phit > 0.1 and resistivity > 10:
            lithology.append('sandstone')
            rule_counts['sandstone'] += 1
        elif vsh >= 0.6:
            lithology.append('shale')
            rule_counts['shale'] += 1
        elif bulk_density > 2.5 and neutron_porosity < 0.15 and vsh < 0.3:
            lithology.append('limestone')
            rule_counts['limestone'] += 1
        else:
            lithology.append('siltstone')
            rule_counts['siltstone'] += 1
    
    # Debug: print rule application statistics
    logging.info("Classification rule applications:")
    for rule, count in rule_counts.items():
        logging.info(f"  {rule}: {count}")
    
    return lithology

def generate_outputs(resampled_df, lithology, output_dir):
    """Generate output files"""
    
    # Save resampled log data
    resampled_output = os.path.join(output_dir, 'resampled_log.csv')
    resampled_df.to_csv(resampled_output, index=False)
    logging.info(f"Saved resampled log data to {resampled_output}")
    
    # Save lithology classification
    litho_df = pd.DataFrame({
        'depth': resampled_df['depth'],
        'lithology': lithology
    })
    litho_output = os.path.join(output_dir, 'lithology_classification.csv')
    litho_df.to_csv(litho_output, index=False)
    logging.info(f"Saved lithology classification to {litho_output}")
    
    # Generate summary statistics - handle NaN values properly
    from collections import Counter
    litho_counts = Counter(lithology)
    
    # Use nanmean to handle NaN values
    mean_porosity = np.nanmean(resampled_df['PHIT'])
    mean_vsh = np.nanmean(resampled_df['Vsh'])
    
    summary = {
        'total_depth_range': f"{resampled_df['depth'].min():.1f}-{resampled_df['depth'].max():.1f}",
        'n_samples': len(resampled_df),
        'layer_counts': dict(litho_counts),
        'mean_porosity': float(mean_porosity) if not np.isnan(mean_porosity) else None,
        'mean_Vsh': float(mean_vsh) if not np.isnan(mean_vsh) else None
    }
    
    summary_output = os.path.join(output_dir, 'summary.json')
    with open(summary_output, 'w') as f:
        json.dump(summary, f, indent=2)
    logging.info(f"Saved summary to {summary_output}")

def main():
    setup_logging()
    args = parse_arguments()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load and resample data
    logging.info(f"Loading data from {args.input}")
    df = load_well_data(args.input)
    
    logging.info(f"Resampling with depth step: {args.depth_step} meters")
    resampled_df = resample_logs(df, args.depth_step)
    
    # Compute derived logs
    logging.info("Computing derived logs (PHIT, Vsh)")
    resampled_df = compute_derived_logs(resampled_df, args.matrix_density)
    
    # Classify lithology
    logging.info("Classifying lithology")
    lithology = classify_lithology(resampled_df)
    
    # Generate outputs
    generate_outputs(resampled_df, lithology, args.output)
    
    print(f"Depth range: {resampled_df['depth'].min():.1f} - {resampled_df['depth'].max():.1f} meters")
    print(f"Number of resampled points: {len(resampled_df)}")
    
    # Print lithology distribution
    from collections import Counter
    litho_counts = Counter(lithology)
    print("Lithology distribution:")
    for litho, count in litho_counts.items():
        print(f"  {litho}: {count}")
    
    mean_porosity = np.nanmean(resampled_df['PHIT'])
    mean_vsh = np.nanmean(resampled_df['Vsh'])
    print(f"Mean porosity: {mean_porosity:.3f}")
    print(f"Mean Vsh: {mean_vsh:.3f}")

if __name__ == "__main__":
    main()
