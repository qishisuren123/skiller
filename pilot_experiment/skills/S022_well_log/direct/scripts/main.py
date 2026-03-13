import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy.interpolate import interp1d

def load_and_validate_data(input_file):
    """Load CSV and validate required columns exist."""
    required_cols = ['depth', 'gamma_ray', 'resistivity', 'neutron_porosity', 'bulk_density', 'caliper']
    
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        raise ValueError(f"Error reading CSV file: {e}")
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Remove rows with NaN in critical columns
    critical_cols = ['depth', 'gamma_ray', 'resistivity', 'neutron_porosity', 'bulk_density']
    df = df.dropna(subset=critical_cols)
    
    if len(df) < 10:
        raise ValueError("Insufficient data points for interpolation (need at least 10)")
    
    return df.sort_values('depth').reset_index(drop=True)

def resample_logs(df, depth_step):
    """Resample all log curves to uniform depth intervals."""
    depth_min = df['depth'].min()
    depth_max = df['depth'].max()
    depth_uniform = np.arange(depth_min, depth_max + depth_step, depth_step)
    
    # Initialize resampled dataframe
    resampled_data = {'depth': depth_uniform}
    
    # Interpolate each log curve
    log_columns = ['gamma_ray', 'resistivity', 'neutron_porosity', 'bulk_density', 'caliper']
    
    for col in log_columns:
        f_interp = interp1d(df['depth'], df[col], kind='linear', 
                           bounds_error=False, fill_value=np.nan)
        resampled_data[col] = f_interp(depth_uniform)
    
    return pd.DataFrame(resampled_data)

def compute_derived_logs(df):
    """Compute PHIT (total porosity) and Vsh (shale volume)."""
    # PHIT calculation: matrix density = 2.65, fluid density = 1.0
    df['PHIT'] = (2.65 - df['bulk_density']) / (2.65 - 1.0)
    df['PHIT'] = np.clip(df['PHIT'], 0, 1)  # Clip to valid porosity range
    
    # Vsh calculation from gamma ray
    gr_min = df['gamma_ray'].min()
    gr_max = df['gamma_ray'].max()
    
    if gr_max > gr_min:
        df['Vsh'] = (df['gamma_ray'] - gr_min) / (gr_max - gr_min)
    else:
        df['Vsh'] = 0.0  # Handle case where all GR values are the same
    
    df['Vsh'] = np.clip(df['Vsh'], 0, 1)  # Clip to valid range
    
    return df

def classify_lithology_row(row):
    """Apply lithology classification rules to a single row."""
    vsh = row['Vsh']
    phit = row['PHIT']
    resistivity = row['resistivity']
    bulk_density = row['bulk_density']
    neutron_por = row['neutron_porosity']
    
    # Apply classification rules in order
    if vsh < 0.3 and phit > 0.1 and resistivity > 10:
        return "sandstone"
    elif vsh >= 0.6:
        return "shale"
    elif bulk_density > 2.5 and neutron_por < 0.15 and vsh < 0.3:
        return "limestone"
    else:
        return "siltstone"

def classify_lithology(df):
    """Classify lithology for all depth samples."""
    lithology_df = pd.DataFrame({
        'depth': df['depth'],
        'lithology': df.apply(classify_lithology_row, axis=1)
    })
    return lithology_df

def generate_summary(df, lithology_df, depth_step):
    """Generate summary statistics."""
    depth_range = df['depth'].max() - df['depth'].min()
    n_samples = len(df)
    
    # Count lithology occurrences
    layer_counts = lithology_df['lithology'].value_counts().to_dict()
    
    # Calculate mean values (excluding NaN)
    mean_porosity = df['PHIT'].mean()
    mean_vsh = df['Vsh'].mean()
    
    summary = {
        'total_depth_range': float(depth_range),
        'n_samples': int(n_samples),
        'depth_step': float(depth_step),
        'layer_counts': layer_counts,
        'mean_porosity': float(mean_porosity),
        'mean_Vsh': float(mean_vsh)
    }
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='Resample well log data and classify lithology')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--depth-step', type=float, default=0.5, help='Depth step in meters (default: 0.5)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Load and validate data
        print(f"Loading data from {args.input}...")
        df = load_and_validate_data(args.input)
        
        # Resample logs
        print(f"Resampling logs with {args.depth_step}m step...")
        resampled_df = resample_logs(df, args.depth_step)
        
        # Compute derived logs
        print("Computing derived logs (PHIT, Vsh)...")
        resampled_df = compute_derived_logs(resampled_df)
        
        # Classify lithology
        print("Classifying lithology...")
        lithology_df = classify_lithology(resampled_df)
        
        # Generate summary
        summary = generate_summary(resampled_df, lithology_df, args.depth_step)
        
        # Save outputs
        resampled_output = os.path.join(args.output, 'resampled_log.csv')
        lithology_output = os.path.join(args.output, 'lithology_classification.csv')
        summary_output = os.path.join(args.output, 'summary.json')
        
        resampled_df.to_csv(resampled_output, index=False)
        lithology_df.to_csv(lithology_output, index=False)
        
        with open(summary_output, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print results
        print(f"\nProcessing complete!")
        print(f"Depth range: {summary['total_depth_range']:.1f} meters")
        print(f"Number of resampled points: {summary['n_samples']}")
        print(f"Lithology distribution:")
        for litho, count in summary['layer_counts'].items():
            percentage = (count / summary['n_samples']) * 100
            print(f"  {litho}: {count} samples ({percentage:.1f}%)")
        
        print(f"\nOutputs saved to {args.output}/")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
