#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Compute crop yield prediction features from field observation data')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--base-temp', type=float, default=10.0, help='Base temperature for GDD calculation (default: 10.0)')
    return parser.parse_args()

def load_data(input_path):
    """Load and validate input CSV data"""
    try:
        df = pd.read_csv(input_path)
        required_columns = ['field_id', 'date', 'ndvi', 'soil_moisture', 'temperature', 'rainfall_mm', 'crop_type', 'yield_tons']
        
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Expected: {required_columns}")
        
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def validate_field_data(df):
    """Validate field data and identify problematic fields"""
    issues = []
    
    for field_id in df['field_id'].unique():
        field_data = df[df['field_id'] == field_id]
        
        if len(field_data) == 0:
            issues.append(f"Field {field_id}: No observations")
            continue
            
        critical_cols = ['temperature', 'ndvi', 'soil_moisture', 'rainfall_mm']
        all_nan_cols = []
        
        for col in critical_cols:
            if field_data[col].isna().all():
                all_nan_cols.append(col)
        
        if all_nan_cols:
            issues.append(f"Field {field_id}: All NaN values in {all_nan_cols}")
    
    return issues

def calculate_gdd(df, base_temp):
    """Calculate Growing Degree Days for each field"""
    df_copy = df.copy()
    df_copy = df_copy.sort_values(['field_id', 'date']).reset_index(drop=True)
    
    print(f"Missing temperature values: {df_copy['temperature'].isna().sum()}")
    
    # Handle NaN temperatures - treat as 0 GDD contribution
    df_copy['gdd_daily'] = np.where(
        df_copy['temperature'].isna(), 
        0,
        np.maximum(0, df_copy['temperature'] - base_temp)
    )
    
    # Calculate cumulative GDD per field
    cumulative_gdd_list = []
    for field_id in df_copy['field_id'].unique():
        field_mask = df_copy['field_id'] == field_id
        field_data = df_copy[field_mask].copy()
        field_data['field_cumulative_gdd'] = field_data['gdd_daily'].cumsum()
        cumulative_gdd_list.extend(field_data['field_cumulative_gdd'].tolist())
    
    df_copy['cumulative_gdd'] = cumulative_gdd_list
    
    print(f"GDD calculation complete. Min cumulative GDD: {df_copy['cumulative_gdd'].min()}")
    print(f"Max cumulative GDD: {df_copy['cumulative_gdd'].max()}")
    
    return df_copy

def calculate_ndvi_stats(df):
    """Calculate NDVI statistics per field with robust NaN handling"""
    ndvi_stats = []
    
    for field_id in df['field_id'].unique():
        field_data = df[df['field_id'] == field_id]
        valid_ndvi = field_data['ndvi'].dropna()
        
        if len(valid_ndvi) == 0:
            stats = {
                'field_id': field_id,
                'mean_ndvi': np.nan,
                'max_ndvi': np.nan,
                'min_ndvi': np.nan,
                'ndvi_std': np.nan,
                'peak_ndvi_date': 'N/A'
            }
        else:
            valid_field_data = field_data.dropna(subset=['ndvi'])
            peak_idx = valid_field_data['ndvi'].idxmax()
            peak_date = valid_field_data.loc[peak_idx, 'date']
            
            stats = {
                'field_id': field_id,
                'mean_ndvi': field_data['ndvi'].mean(),
                'max_ndvi': field_data['ndvi'].max(),
                'min_ndvi': field_data['ndvi'].min(),
                'ndvi_std': field_data['ndvi'].std(),
                'peak_ndvi_date': peak_date.strftime('%Y-%m-%d')
            }
        
        ndvi_stats.append(stats)
    
    return pd.DataFrame(ndvi_stats)

def create_feature_matrix(df):
    """Create the final feature matrix with one row per field"""
    field_agg = df.groupby('field_id').agg({
        'crop_type': 'first',
        'rainfall_mm': 'sum',
        'soil_moisture': 'mean',
        'cumulative_gdd': 'last',  # Use 'last' not 'max' for time series
        'yield_tons': 'first'
    }).reset_index()
    
    field_agg = field_agg.rename(columns={
        'rainfall_mm': 'total_rainfall',
        'soil_moisture': 'mean_soil_moisture'
    })
    
    ndvi_stats = calculate_ndvi_stats(df)
    feature_matrix = field_agg.merge(ndvi_stats, on='field_id')
    
    column_order = ['field_id', 'crop_type', 'mean_ndvi', 'max_ndvi', 'min_ndvi', 'ndvi_std', 
                   'peak_ndvi_date', 'total_rainfall', 'mean_soil_moisture', 
                   'cumulative_gdd', 'yield_tons']
    
    return feature_matrix[column_order]

def calculate_correlation_matrix(feature_matrix):
    """Calculate Pearson correlation matrix for numeric features"""
    numeric_cols = ['mean_ndvi', 'max_ndvi', 'min_ndvi', 'ndvi_std', 'total_rainfall', 
                   'mean_soil_moisture', 'cumulative_gdd', 'yield_tons']
    
    numeric_data = feature_matrix[numeric_cols]
    correlation_matrix = numeric_data.corr()
    
    return correlation_matrix

def generate_summary(feature_matrix, correlation_matrix):
    """Generate summary statistics and insights"""
    yield_corrs = correlation_matrix['yield_tons'].drop('yield_tons').abs().sort_values(ascending=False)
    top_3_correlates = yield_corrs.head(3).to_dict()
    
    summary = {
        'n_fields': len(feature_matrix),
        'n_crop_types': feature_matrix['crop_type'].nunique(),
        'feature_names': correlation_matrix.columns.tolist(),
        'top_3_yield_correlates': {
            feature: round(corr, 4) for feature, corr in top_3_correlates.items()
        }
    }
    
    return summary

def main():
    args = parse_arguments()
    
    os.makedirs(args.output, exist_ok=True)
    
    df = load_data(args.input)
    if df is None:
        return
    
    print(f"Loaded {len(df)} observations from {args.input}")
    print(f"Processing {df['field_id'].nunique()} unique fields...")
    
    # Validate data quality
    issues = validate_field_data(df)
    if issues:
        print("Data quality issues found:")
        for issue in issues[:5]:  # Show first 5 issues
            print(f"  - {issue}")
        if len(issues) > 5:
            print(f"  ... and {len(issues) - 5} more issues")
    
    df_with_gdd = calculate_gdd(df, args.base_temp)
    feature_matrix = create_feature_matrix(df_with_gdd)
    correlation_matrix = calculate_correlation_matrix(feature_matrix)
    summary = generate_summary(feature_matrix, correlation_matrix)
    
    # Save outputs
    feature_path = os.path.join(args.output, 'field_features.csv')
    corr_path = os.path.join(args.output, 'correlation_matrix.csv')
    summary_path = os.path.join(args.output, 'summary.json')
    
    feature_matrix.to_csv(feature_path, index=False)
    correlation_matrix.to_csv(corr_path)
    
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    strongest_correlate = list(summary['top_3_yield_correlates'].keys())[0]
    strongest_corr = list(summary['top_3_yield_correlates'].values())[0]
    
    print(f"\nProcessed {summary['n_fields']} fields with {summary['n_crop_types']} crop types")
    print(f"Strongest yield correlate: {strongest_correlate} (r={strongest_corr})")
    print(f"\nOutputs saved to {args.output}/")

if __name__ == "__main__":
    main()
