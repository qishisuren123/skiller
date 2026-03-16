#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_growing_degree_days(df, base_temp):
    """Compute cumulative growing degree days per field - optimized"""
    logger.info(f"Computing growing degree days with base temperature {base_temp}°C")
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['field_id', 'date'])
    
    # Vectorized GDD calculation
    df['gdd_daily'] = np.maximum(0, df['temperature'] - base_temp)
    
    # More efficient cumulative sum using transform
    df['cumulative_gdd'] = df.groupby('field_id')['gdd_daily'].transform('cumsum')
    
    return df

def create_feature_matrix_optimized(df):
    """Create feature matrix with optimized aggregations"""
    logger.info("Creating feature matrix with optimized aggregations")
    
    # Single groupby operation for all basic aggregations
    agg_dict = {
        'crop_type': 'first',
        'yield_tons': 'first', 
        'rainfall_mm': 'sum',
        'soil_moisture': 'mean',
        'cumulative_gdd': 'max',
        'ndvi': ['mean', 'max', 'min', 'std', 'count']
    }
    
    # Perform all aggregations at once
    features = df.groupby('field_id').agg(agg_dict)
    
    # Flatten column names
    features.columns = ['crop_type', 'yield_tons', 'total_rainfall', 'mean_soil_moisture',
                       'cumulative_gdd', 'mean_ndvi', 'max_ndvi', 'min_ndvi', 'ndvi_std', 'ndvi_count']
    
    # Handle NaN values for single observations efficiently
    features['ndvi_std'] = features['ndvi_std'].fillna(0.0)
    
    # Find peak NDVI dates efficiently using vectorized operations
    peak_ndvi_data = df.loc[df.groupby('field_id')['ndvi'].transform('max') == df['ndvi']]
    peak_dates = peak_ndvi_data.groupby('field_id')['date'].first()
    features['peak_ndvi_date'] = peak_dates
    
    # Drop the count column as it was just for debugging
    features = features.drop('ndvi_count', axis=1)
    
    # Round numeric columns
    numeric_cols = ['total_rainfall', 'mean_soil_moisture', 'cumulative_gdd', 
                   'mean_ndvi', 'max_ndvi', 'min_ndvi', 'ndvi_std']
    features[numeric_cols] = features[numeric_cols].round(4)
    
    # Reset index
    features = features.reset_index()
    
    # Log any NaN issues
    nan_counts = features.isnull().sum()
    if nan_counts.any():
        logger.warning("NaN values found in features:")
        for col, count in nan_counts[nan_counts > 0].items():
            logger.warning(f"  {col}: {count} NaN values")
    
    return features

def compute_correlations(features):
    """Compute Pearson correlation matrix for numeric features"""
    logger.info("Computing correlation matrix")
    # Select only numeric columns
    numeric_cols = ['yield_tons', 'total_rainfall', 'mean_soil_moisture', 'cumulative_gdd', 
                   'mean_ndvi', 'max_ndvi', 'min_ndvi', 'ndvi_std']
    
    numeric_features = features[numeric_cols]
    
    # Always use pandas correlation to avoid numpy broadcasting issues
    if not numeric_features.isnull().any().any():
        logger.info("Computing correlation matrix with pandas")
        correlation_matrix = numeric_features.corr(method='pearson')
    else:
        logger.warning("NaN values detected, using pandas correlation with pairwise complete observations")
        correlation_matrix = numeric_features.corr(method='pearson', min_periods=1)
    
    return correlation_matrix

def create_summary(features, correlation_matrix):
    """Create summary statistics"""
    logger.info("Creating summary statistics")
    # Get yield correlations (excluding self-correlation)
    yield_corrs = correlation_matrix['yield_tons'].drop('yield_tons')
    
    # Remove NaN correlations and get absolute values
    yield_corrs_clean = yield_corrs.dropna().abs().sort_values(ascending=False)
    
    if len(yield_corrs_clean) == 0:
        logger.warning("No valid correlations found with yield")
        top_3_correlates = {}
    else:
        # Convert to dict manually
        top_3_correlates = {}
        for feature, corr_val in yield_corrs_clean.head(3).items():
            top_3_correlates[feature] = float(corr_val)
    
    summary = {
        'n_fields': int(len(features)),
        'n_crop_types': int(features['crop_type'].nunique()),
        'feature_names': list(correlation_matrix.columns),
        'top_3_yield_correlates': top_3_correlates
    }
    
    return summary

def main():
    parser = argparse.ArgumentParser(description='Compute crop yield prediction features')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--base-temp', type=float, default=10.0, help='Base temperature for GDD calculation')
    
    args = parser.parse_args()
    
    start_time = datetime.now()
    logger.info(f"Starting processing at {start_time}")
    logger.info(f"Loading data from {args.input}")
    
    # Load data
    df = pd.read_csv(args.input)
    logger.info(f"Loaded {len(df)} records from {df['field_id'].nunique()} fields")
    
    # Compute GDD
    df = compute_growing_degree_days(df, args.base_temp)
    
    # Create feature matrix with optimized method
    features = create_feature_matrix_optimized(df)
    
    # Compute correlations
    correlation_matrix = compute_correlations(features)
    
    # Create summary
    summary = create_summary(features, correlation_matrix)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    logger.info(f"Saving outputs to {args.output}")
    
    # Save outputs
    features.to_csv(os.path.join(args.output, 'field_features.csv'), index=False)
    correlation_matrix.to_csv(os.path.join(args.output, 'correlation_matrix.csv'))
    
    with open(os.path.join(args.output, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    end_time = datetime.now()
    processing_time = end_time - start_time
    
    if summary['top_3_yield_correlates']:
        strongest_correlate = list(summary['top_3_yield_correlates'].keys())[0]
        print(f"Processed {summary['n_fields']} fields in {processing_time}")
        print(f"Strongest yield correlate: {strongest_correlate}")
    else:
        print(f"Processed {summary['n_fields']} fields in {processing_time}")
        print("Warning: No valid yield correlations found")
    
    logger.info(f"Processing completed successfully in {processing_time}")

if __name__ == "__main__":
    main()
