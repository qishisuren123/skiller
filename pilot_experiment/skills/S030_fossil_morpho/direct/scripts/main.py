import argparse
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

def calculate_shape_indices(df):
    """Calculate morphometric shape indices for fossil specimens."""
    # Elongation = length / width
    df['elongation'] = df['length_mm'] / df['width_mm']
    
    # Flatness = width / height
    df['flatness'] = df['width_mm'] / df['height_mm']
    
    # Krumbein sphericity approximation
    df['sphericity'] = np.power(df['width_mm'] * df['height_mm'], 1/3) / df['length_mm']
    
    # Estimated volume as ellipsoid (mm³)
    df['volume_mm3'] = (4/3) * np.pi * (df['length_mm']/2) * (df['width_mm']/2) * (df['height_mm']/2)
    
    # Convert volume to cm³ and calculate density
    df['volume_cm3'] = df['volume_mm3'] / 1000
    df['density_g_cm3'] = df['mass_g'] / df['volume_cm3']
    
    return df

def perform_pca(data):
    """Perform PCA using numpy eigen-decomposition."""
    # Z-score standardization
    standardized = (data - np.mean(data, axis=0)) / np.std(data, axis=0)
    
    # Compute covariance matrix and eigen-decomposition
    cov_matrix = np.cov(standardized.T)
    eigenvals, eigenvecs = np.linalg.eigh(cov_matrix)
    
    # Sort by eigenvalue descending
    idx = np.argsort(eigenvals)[::-1]
    eigenvals = eigenvals[idx]
    eigenvecs = eigenvecs[:, idx]
    
    # Calculate explained variance ratios
    explained_var = eigenvals / np.sum(eigenvals)
    
    # Calculate PC scores
    pc_scores = standardized @ eigenvecs
    
    return pc_scores, eigenvecs, explained_var

def compute_group_statistics(df, group_col, measurement_cols):
    """Compute mean and std statistics for grouped data."""
    stats = {}
    for group in df[group_col].unique():
        group_data = df[df[group_col] == group][measurement_cols]
        stats[group] = {
            'n_specimens': len(group_data),
            'means': group_data.mean().to_dict(),
            'stds': group_data.std().to_dict()
        }
    return stats

def main():
    parser = argparse.ArgumentParser(description='Perform morphometric analysis on fossil specimens')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = pd.read_csv(args.input)
        
        # Validate required columns
        required_cols = ['specimen_id', 'taxon', 'length_mm', 'width_mm', 'height_mm', 'mass_g', 'formation', 'epoch']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Validate measurements (no negative values or zeros)
        measurement_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g']
        for col in measurement_cols:
            if (df[col] <= 0).any():
                print(f"Warning: Found non-positive values in {col}, setting to NaN")
                df.loc[df[col] <= 0, col] = np.nan
        
        # Calculate shape indices
        df = calculate_shape_indices(df)
        
        # Prepare data for PCA (remove NaN rows)
        pca_data = df[measurement_cols].dropna()
        pca_indices = pca_data.index
        
        if len(pca_data) < 4:
            raise ValueError("Insufficient valid data points for PCA analysis")
        
        # Perform PCA
        pc_scores, loadings, explained_var = perform_pca(pca_data.values)
        
        # Add PC scores to dataframe
        for i in range(4):
            df.loc[pca_indices, f'PC{i+1}'] = pc_scores[:, i]
        
        # Create PCA results dataframe
        pca_results = pd.DataFrame({
            'component': [f'PC{i+1}' for i in range(4)],
            'explained_variance_ratio': explained_var,
            'length_loading': loadings[0, :],
            'width_loading': loadings[1, :],
            'height_loading': loadings[2, :],
            'mass_loading': loadings[3, :]
        })
        
        # Calculate group statistics
        shape_indices = ['elongation', 'flatness', 'sphericity', 'density_g_cm3']
        all_metrics = measurement_cols + shape_indices
        
        taxon_stats = compute_group_statistics(df, 'taxon', all_metrics)
        epoch_stats = compute_group_statistics(df, 'epoch', all_metrics)
        
        summary_stats = {
            'by_taxon': taxon_stats,
            'by_epoch': epoch_stats
        }
        
        # Convert numpy types to native Python types for JSON serialization
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {k: convert_numpy_types(v) for k, v in obj.items()}
            elif isinstance(obj, (np.integer, np.floating)):
                return obj.item()
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            return obj
        
        summary_stats = convert_numpy_types(summary_stats)
        
        # Save outputs
        df.to_csv(output_dir / 'morphometrics.csv', index=False)
        pca_results.to_csv(output_dir / 'pca_results.csv', index=False)
        
        with open(output_dir / 'taxon_summary.json', 'w') as f:
            json.dump(summary_stats, f, indent=2)
        
        # Print summary
        n_specimens = len(df)
        n_taxa = df['taxon'].nunique()
        dominant_taxon = df['taxon'].value_counts().index[0]
        pc12_variance = explained_var[:2].sum()
        
        print(f"Morphometric Analysis Summary:")
        print(f"Number of specimens: {n_specimens}")
        print(f"Number of taxa: {n_taxa}")
        print(f"Dominant taxon: {dominant_taxon}")
        print(f"PCA variance explained by PC1-PC2: {pc12_variance:.3f}")
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
