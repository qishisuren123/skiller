import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Compute crop yield prediction features from field data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--base-temp', type=float, default=10.0, help='Base temperature for GDD calculation')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load and validate data
    try:
        df = pd.read_csv(args.input)
    except FileNotFoundError:
        print(f"Error: Input file {args.input} not found")
        return
    
    required_cols = ['field_id', 'date', 'ndvi', 'soil_moisture', 'temperature', 'rainfall_mm', 'crop_type', 'yield_tons']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return
    
    # Parse dates and sort
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['field_id', 'date'])
    
    # Calculate Growing Degree Days
    df['gdd_daily'] = np.maximum(0, df['temperature'] - args.base_temp)
    df['cumulative_gdd'] = df.groupby('field_id')['gdd_daily'].cumsum()
    
    # Aggregate features per field
    # NDVI statistics
    ndvi_stats = df.groupby('field_id')['ndvi'].agg(['mean', 'max', 'min', 'std']).reset_index()
    ndvi_stats.columns = ['field_id', 'mean_ndvi', 'max_ndvi', 'min_ndvi', 'ndvi_std']
    
    # Peak NDVI dates
    peak_ndvi_idx = df.groupby('field_id')['ndvi'].idxmax()
    peak_dates = df.loc[peak_ndvi_idx][['field_id', 'date']].copy()
    peak_dates['peak_ndvi_date'] = peak_dates['date'].dt.strftime('%Y-%m-%d')
    peak_dates = peak_dates[['field_id', 'peak_ndvi_date']]
    
    # Other aggregations
    field_aggs = df.groupby('field_id').agg({
        'crop_type': 'first',
        'rainfall_mm': 'sum',
        'soil_moisture': 'mean',
        'cumulative_gdd': 'max',
        'yield_tons': 'first'
    }).reset_index()
    
    field_aggs.columns = ['field_id', 'crop_type', 'total_rainfall', 'mean_soil_moisture', 'cumulative_gdd', 'yield_tons']
    
    # Merge all features
    features = field_aggs.merge(ndvi_stats, on='field_id').merge(peak_dates, on='field_id')
    
    # Reorder columns for final feature matrix
    feature_cols = ['field_id', 'crop_type', 'mean_ndvi', 'max_ndvi', 'ndvi_std', 
                   'peak_ndvi_date', 'total_rainfall', 'mean_soil_moisture', 
                   'cumulative_gdd', 'yield_tons']
    features = features[feature_cols]
    
    # Compute correlation matrix
    numeric_features = features.select_dtypes(include=[np.number])
    correlation_matrix = numeric_features.corr()
    
    # Find top yield correlates
    yield_corr = correlation_matrix['yield_tons'].abs().sort_values(ascending=False)
    top_yield_correlates = yield_corr.drop('yield_tons').head(3).index.tolist()
    
    # Save outputs
    features.to_csv(os.path.join(args.output, 'field_features.csv'), index=False)
    correlation_matrix.to_csv(os.path.join(args.output, 'correlation_matrix.csv'))
    
    # Create summary
    summary = {
        'n_fields': len(features),
        'n_crop_types': features['crop_type'].nunique(),
        'feature_names': numeric_features.columns.tolist(),
        'top_3_yield_correlates': top_yield_correlates
    }
    
    with open(os.path.join(args.output, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    strongest_correlate = top_yield_correlates[0] if top_yield_correlates else "None"
    print(f"Processed {summary['n_fields']} fields across {summary['n_crop_types']} crop types")
    print(f"Strongest yield correlate: {strongest_correlate}")
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
