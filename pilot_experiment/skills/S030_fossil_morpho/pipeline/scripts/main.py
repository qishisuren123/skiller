#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from math import pi

def calculate_shape_indices(df):
    """Calculate morphometric shape indices for each specimen"""
    
    # Check for problematic values first
    print("Checking for problematic values...")
    
    # Check for zeros or negative values
    measurement_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g']
    for col in measurement_cols:
        zeros = (df[col] == 0).sum()
        negatives = (df[col] < 0).sum()
        if zeros > 0:
            print(f"Warning: {zeros} specimens have {col} = 0")
        if negatives > 0:
            print(f"Warning: {negatives} specimens have negative {col}")
    
    # Show problematic specimens
    problematic = df[(df['length_mm'] <= 0) | (df['width_mm'] <= 0) | 
                     (df['height_mm'] <= 0) | (df['mass_g'] <= 0)]
    if len(problematic) > 0:
        print(f"Found {len(problematic)} specimens with zero/negative measurements:")
        print(problematic[['specimen_id'] + measurement_cols])
    
    # Elongation = length_mm / width_mm (handle division by zero)
    df['elongation'] = np.where(df['width_mm'] > 0, 
                               df['length_mm'] / df['width_mm'], 
                               np.nan)
    
    # Flatness = width_mm / height_mm (handle division by zero)
    df['flatness'] = np.where(df['height_mm'] > 0,
                             df['width_mm'] / df['height_mm'],
                             np.nan)
    
    # Sphericity = (width_mm * height_mm)^(1/3) / length_mm (handle zeros and division)
    numerator = np.where((df['width_mm'] > 0) & (df['height_mm'] > 0),
                        (df['width_mm'] * df['height_mm']) ** (1/3),
                        np.nan)
    df['sphericity'] = np.where(df['length_mm'] > 0,
                               numerator / df['length_mm'],
                               np.nan)
    
    # Estimated volume as ellipsoid = (4/3) * pi * (length/2) * (width/2) * (height/2)
    df['volume_mm3'] = np.where((df['length_mm'] > 0) & (df['width_mm'] > 0) & (df['height_mm'] > 0),
                               (4/3) * pi * (df['length_mm']/2) * (df['width_mm']/2) * (df['height_mm']/2),
                               np.nan)
    
    # Density = mass_g / volume (convert mm^3 to cm^3: divide by 1000)
    df['density_g_cm3'] = np.where(df['volume_mm3'] > 0,
                                  df['mass_g'] / (df['volume_mm3'] / 1000),
                                  np.nan)
    
    # Report how many NaN values were created
    shape_indices = ['elongation', 'flatness', 'sphericity', 'density_g_cm3']
    for col in shape_indices:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            print(f"Warning: {nan_count} specimens have NaN {col} due to invalid measurements")
    
    return df

def perform_pca(df):
    """Perform PCA on the 4 measurement columns using numpy eigen-decomposition"""
    
    # Extract the 4 measurement columns
    measurement_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g']
    
    # Check for missing values in measurement columns
    print("Checking measurement data for PCA...")
    for col in measurement_cols:
        missing = df[col].isna().sum()
        if missing > 0:
            print(f"Warning: {missing} specimens have missing {col}")
    
    # Remove specimens with any missing measurement values
    df_clean = df.dropna(subset=measurement_cols)
    n_removed = len(df) - len(df_clean)
    if n_removed > 0:
        print(f"Removed {n_removed} specimens with missing measurements for PCA")
    
    if len(df_clean) == 0:
        raise ValueError("No specimens remaining after removing missing values")
    
    # Check if we have enough specimens for meaningful PCA
    if len(df_clean) < 2:
        print(f"Warning: Only {len(df_clean)} specimens available for PCA. Cannot perform meaningful analysis.")
        # Set all PC scores to NaN
        for i in range(4):
            df[f'PC{i+1}'] = np.nan
        
        # Return empty PCA results
        pca_results = pd.DataFrame({
            'component': [f'PC{i+1}' for i in range(4)],
            'explained_variance_ratio': [np.nan] * 4,
            'length_loading': [np.nan] * 4,
            'width_loading': [np.nan] * 4,
            'height_loading': [np.nan] * 4,
            'mass_loading': [np.nan] * 4
        })
        return df, pca_results
    
    X = df_clean[measurement_cols].values
    
    # Z-score standardization
    X_mean = np.mean(X, axis=0)
    X_std = np.std(X, axis=0)
    
    # Check for zero standard deviation
    zero_std_cols = [measurement_cols[i] for i, std in enumerate(X_std) if std == 0]
    if zero_std_cols:
        print(f"Warning: Zero standard deviation in columns: {zero_std_cols}")
        # Add small epsilon to avoid division by zero
        X_std = np.where(X_std == 0, 1e-10, X_std)
    
    X_standardized = (X - X_mean) / X_std
    
    # Calculate covariance matrix
    cov_matrix = np.cov(X_standardized.T)
    
    # Eigen-decomposition
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    # Sort by eigenvalues (descending)
    idx = np.argsort(eigenvalues)[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]
    
    # Calculate explained variance ratios
    explained_variance_ratio = eigenvalues / np.sum(eigenvalues)
    
    # Project data onto principal components
    pc_scores = X_standardized @ eigenvectors
    
    # Add PC scores back to original dataframe (with NaN for removed specimens)
    for i in range(4):
        df[f'PC{i+1}'] = np.nan
        df.loc[df_clean.index, f'PC{i+1}'] = pc_scores[:, i]
    
    # Create PCA results dataframe
    pca_results = pd.DataFrame({
        'component': [f'PC{i+1}' for i in range(4)],
        'explained_variance_ratio': explained_variance_ratio,
        'length_loading': eigenvectors[0, :],
        'width_loading': eigenvectors[1, :],
        'height_loading': eigenvectors[2, :],
        'mass_loading': eigenvectors[3, :]
    })
    
    print(f"PCA completed on {len(df_clean)} specimens")
    
    return df, pca_results

def calculate_group_statistics(df):
    """Calculate summary statistics by taxon and epoch"""
    
    # Columns to summarize (measurements + shape indices)
    summary_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g', 
                   'elongation', 'flatness', 'sphericity', 'density_g_cm3']
    
    summary_data = {}
    
    # Taxon statistics
    summary_data['taxon'] = {}
    for taxon in df['taxon'].unique():
        taxon_data = df[df['taxon'] == taxon]
        taxon_stats = {
            'n_specimens': len(taxon_data)
        }
        
        for col in summary_cols:
            # Use pandas methods that automatically handle NaN
            valid_data = taxon_data[col].dropna()
            taxon_stats[f'{col}_n_valid'] = len(valid_data)
            
            if len(valid_data) > 0:
                taxon_stats[f'{col}_mean'] = float(valid_data.mean())
                taxon_stats[f'{col}_std'] = float(valid_data.std()) if len(valid_data) > 1 else 0.0
            else:
                taxon_stats[f'{col}_mean'] = None
                taxon_stats[f'{col}_std'] = None
        
        summary_data['taxon'][taxon] = taxon_stats
    
    # Epoch statistics
    summary_data['epoch'] = {}
    for epoch in df['epoch'].unique():
        epoch_data = df[df['epoch'] == epoch]
        epoch_stats = {
            'n_specimens': len(epoch_data)
        }
        
        for col in summary_cols:
            # Use pandas methods that automatically handle NaN
            valid_data = epoch_data[col].dropna()
            epoch_stats[f'{col}_n_valid'] = len(valid_data)
            
            if len(valid_data) > 0:
                epoch_stats[f'{col}_mean'] = float(valid_data.mean())
                epoch_stats[f'{col}_std'] = float(valid_data.std()) if len(valid_data) > 1 else 0.0
            else:
                epoch_stats[f'{col}_mean'] = None
                epoch_stats[f'{col}_std'] = None
        
        summary_data['epoch'][epoch] = epoch_stats
    
    # Print summary of data quality
    print("\nData quality summary:")
    for col in summary_cols:
        total_valid = df[col].notna().sum()
        total_specimens = len(df)
        print(f"{col}: {total_valid}/{total_specimens} valid values ({100*total_valid/total_specimens:.1f}%)")
    
    return summary_data

def main():
    parser = argparse.ArgumentParser(description='Perform morphometric analysis on fossil specimens')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--output', required=True, help='Output directory path')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Read the CSV data
    try:
        df = pd.read_csv(args.input)
        print(f"Loaded {len(df)} specimens from {args.input}")
    except FileNotFoundError:
        print(f"Error: Input file {args.input} not found")
        return
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return
    
    # Validate required columns
    required_cols = ['specimen_id', 'taxon', 'length_mm', 'width_mm', 'height_mm', 'mass_g', 'formation', 'epoch']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return
    
    print(f"Data validation passed. Processing {len(df)} specimens...")
    
    # Calculate shape indices
    df = calculate_shape_indices(df)
    print("Shape indices calculated successfully")
    
    # Perform PCA
    df, pca_results = perform_pca(df)
    print("PCA analysis completed")
    
    # Calculate group statistics
    summary_data = calculate_group_statistics(df)
    print("Group statistics calculated")
    
    # Generate outputs
    morphometrics_path = os.path.join(args.output, 'morphometrics.csv')
    pca_path = os.path.join(args.output, 'pca_results.csv')
    summary_path = os.path.join(args.output, 'taxon_summary.json')
    
    df.to_csv(morphometrics_path, index=False)
    pca_results.to_csv(pca_path, index=False)
    
    with open(summary_path, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    # Print summary
    n_specimens = len(df)
    n_taxa = df['taxon'].nunique()
    dominant_taxon = df['taxon'].value_counts().index[0]
    pc12_variance = pca_results['explained_variance_ratio'].iloc[:2].sum()
    
    print(f"\n=== ANALYSIS SUMMARY ===")
    print(f"Number of specimens: {n_specimens}")
    print(f"Number of taxa: {n_taxa}")
    print(f"Dominant taxon: {dominant_taxon}")
    print(f"PCA variance explained by PC1-PC2: {pc12_variance:.3f}")
    print(f"\nOutputs saved to {args.output}/")

if __name__ == "__main__":
    main()
