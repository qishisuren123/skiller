#!/usr/bin/env python3
"""
Morphometric analysis CLI for fossil specimen measurements
"""

import argparse
import pandas as pd
import numpy as np
import json
import os
import logging
from pathlib import Path
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compute_shape_indices(df):
    """Compute morphometric shape indices with data validation"""
    logging.info("Computing shape indices with data validation")
    
    # Check for non-positive measurements
    measurement_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g']
    for col in measurement_cols:
        non_positive = (df[col] <= 0) & df[col].notna()
        if non_positive.any():
            n_invalid = non_positive.sum()
            logging.warning(f"Found {n_invalid} non-positive values in {col}, setting to NaN")
            df.loc[non_positive, col] = np.nan
    
    # Elongation = length / width (avoid division by zero)
    df['elongation'] = np.where(
        (df['width_mm'] > 0) & df['width_mm'].notna() & df['length_mm'].notna(),
        df['length_mm'] / df['width_mm'],
        np.nan
    )
    
    # Flatness = width / height (avoid division by zero)
    df['flatness'] = np.where(
        (df['height_mm'] > 0) & df['height_mm'].notna() & df['width_mm'].notna(),
        df['width_mm'] / df['height_mm'],
        np.nan
    )
    
    # Sphericity (Krumbein approximation) - need all dimensions positive
    valid_for_sphericity = (
        (df['width_mm'] > 0) & df['width_mm'].notna() &
        (df['height_mm'] > 0) & df['height_mm'].notna() &
        (df['length_mm'] > 0) & df['length_mm'].notna()
    )
    df['sphericity'] = np.where(
        valid_for_sphericity,
        (df['width_mm'] * df['height_mm']) ** (1/3) / df['length_mm'],
        np.nan
    )
    
    # Estimated volume as ellipsoid - need all dimensions positive
    valid_for_volume = (
        (df['length_mm'] > 0) & df['length_mm'].notna() &
        (df['width_mm'] > 0) & df['width_mm'].notna() &
        (df['height_mm'] > 0) & df['height_mm'].notna()
    )
    df['volume_mm3'] = np.where(
        valid_for_volume,
        (4/3) * np.pi * (df['length_mm']/2) * (df['width_mm']/2) * (df['height_mm']/2),
        np.nan
    )
    
    # Density (convert mm³ to cm³) - need positive mass and volume
    valid_for_density = (
        valid_for_volume & 
        (df['mass_g'] > 0) & df['mass_g'].notna() &
        (df['volume_mm3'] > 0) & df['volume_mm3'].notna()
    )
    df['density_g_cm3'] = np.where(
        valid_for_density,
        df['mass_g'] / (df['volume_mm3'] / 1000),
        np.nan
    )
    
    # Log validation results
    shape_indices = ['elongation', 'flatness', 'sphericity', 'volume_mm3', 'density_g_cm3']
    for idx in shape_indices:
        n_valid = df[idx].notna().sum()
        n_total = len(df)
        logging.info(f"{idx}: {n_valid}/{n_total} valid values ({n_valid/n_total*100:.1f}%)")
    
    return df

def perform_pca(df):
    """Perform memory-efficient PCA using sklearn"""
    measurement_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g']
    measurements_df = df[measurement_cols].dropna()
    
    if len(measurements_df) == 0:
        raise ValueError("No complete measurement records found")
    
    logging.info(f"Using {len(measurements_df)} complete records for PCA")
    
    # Use sklearn for memory-efficient PCA
    scaler = StandardScaler()
    pca = PCA(n_components=4)
    
    # Fit and transform
    standardized = scaler.fit_transform(measurements_df.values)
    pc_scores = pca.fit_transform(standardized)
    
    # Create full PC scores array with NaN for missing data
    full_pc_scores = np.full((len(df), 4), np.nan)
    valid_indices = df[measurement_cols].dropna().index
    full_pc_scores[valid_indices] = pc_scores
    
    return full_pc_scores, pca.components_, pca.explained_variance_ratio_

def compute_group_statistics(df):
    """Compute statistics grouped by taxon and epoch"""
    measurement_cols = ['length_mm', 'width_mm', 'height_mm', 'mass_g']
    shape_cols = ['elongation', 'flatness', 'sphericity', 'volume_mm3', 'density_g_cm3']
    all_numeric_cols = measurement_cols + shape_cols
    
    summary = {}
    
    # Statistics by taxon
    summary['by_taxon'] = {}
    for taxon in df['taxon'].unique():
        taxon_data = df[df['taxon'] == taxon]
        taxon_stats = {'n_specimens': len(taxon_data)}
        
        for col in all_numeric_cols:
            values = taxon_data[col].dropna()
            if len(values) > 0:
                taxon_stats[f'{col}_mean'] = float(values.mean())
                taxon_stats[f'{col}_std'] = float(values.std())
            else:
                taxon_stats[f'{col}_mean'] = None
                taxon_stats[f'{col}_std'] = None
        
        summary['by_taxon'][taxon] = taxon_stats
    
    # Statistics by epoch
    summary['by_epoch'] = {}
    for epoch in df['epoch'].unique():
        epoch_data = df[df['epoch'] == epoch]
        epoch_stats = {'n_specimens': len(epoch_data)}
        
        for col in all_numeric_cols:
            values = epoch_data[col].dropna()
            if len(values) > 0:
                epoch_stats[f'{col}_mean'] = float(values.mean())
                epoch_stats[f'{col}_std'] = float(values.std())
            else:
                epoch_stats[f'{col}_mean'] = None
                epoch_stats[f'{col}_std'] = None
        
        summary['by_epoch'][epoch] = epoch_stats
    
    return summary

def print_summary(df, explained_var):
    """Print analysis summary"""
    n_specimens = len(df)
    n_taxa = df['taxon'].nunique()
    
    taxon_counts = df['taxon'].value_counts()
    dominant_taxon = taxon_counts.index[0]
    dominant_count = taxon_counts.iloc[0]
    
    pc12_variance = explained_var[:2].sum()
    
    print("\n" + "="*50)
    print("MORPHOMETRIC ANALYSIS SUMMARY")
    print("="*50)
    print(f"Number of specimens: {n_specimens}")
    print(f"Number of taxa: {n_taxa}")
    print(f"Dominant taxon: {dominant_taxon} ({dominant_count} specimens)")
    print(f"PCA variance explained by PC1-PC2: {pc12_variance:.3f} ({pc12_variance*100:.1f}%)")
    print("="*50)

def main():
    parser = argparse.ArgumentParser(description='Morphometric analysis of fossil specimens')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    
    args = parser.parse_args()
    
    setup_logging()
    logging.info("Starting morphometric analysis")
    
    # Read input data
    df = pd.read_csv(args.input)
    logging.info(f"Loaded {len(df)} specimens")
    
    # Check for missing values
    missing_counts = df.isnull().sum()
    if missing_counts.any():
        logging.warning(f"Missing values found:\n{missing_counts[missing_counts > 0]}")
    
    # Compute shape indices
    df = compute_shape_indices(df)
    
    # Perform PCA
    pc_scores, loadings, explained_var = perform_pca(df)
    
    # Add PC scores to dataframe
    for i in range(4):
        df[f'PC{i+1}'] = pc_scores[:, i]
    
    # Compute group statistics
    group_stats = compute_group_statistics(df)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Save morphometrics results
    df.to_csv(os.path.join(args.output, 'morphometrics.csv'), index=False)
    
    # Save PCA results
    pca_results = []
    for i in range(4):
        pca_results.append({
            'component': f'PC{i+1}',
            'explained_variance_ratio': explained_var[i],
            'length_loading': loadings[0, i],
            'width_loading': loadings[1, i],
            'height_loading': loadings[2, i],
            'mass_loading': loadings[3, i]
        })
    
    pca_df = pd.DataFrame(pca_results)
    pca_df.to_csv(os.path.join(args.output, 'pca_results.csv'), index=False)
    
    # Save group statistics as JSON
    with open(os.path.join(args.output, 'taxon_summary.json'), 'w') as f:
        json.dump(group_stats, f, indent=2)
    
    # Print summary
    print_summary(df, explained_var)
    
    logging.info("Analysis complete")

if __name__ == '__main__':
    main()
