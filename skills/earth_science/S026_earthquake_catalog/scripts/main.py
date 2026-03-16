#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import logging
from math import radians, cos, sin, asin, sqrt, log10, e

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in km"""
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def haversine_vectorized(lat1, lon1, lat2, lon2):
    """Vectorized haversine distance calculation"""
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    return c * r

def estimate_completeness_magnitude(magnitudes, bin_width=0.1):
    """Estimate magnitude of completeness from maximum of magnitude-frequency histogram"""
    min_mag = np.floor(magnitudes.min() * 10) / 10
    max_mag = np.ceil(magnitudes.max() * 10) / 10
    n_bins = int((max_mag - min_mag) / bin_width) + 1
    bins = np.linspace(min_mag, max_mag, n_bins + 1)
    hist, bin_edges = np.histogram(magnitudes, bins=bins)
    max_freq_idx = np.argmax(hist)
    completeness_mag = bin_edges[max_freq_idx]
    return completeness_mag

def calculate_b_value(magnitudes, completeness_mag, bin_width=0.1):
    """Calculate Gutenberg-Richter b-value using Aki formula"""
    complete_mags = magnitudes[magnitudes >= completeness_mag]
    if len(complete_mags) <= 1:
        return np.nan
    
    mean_mag = np.mean(complete_mags)
    denominator = mean_mag - completeness_mag + bin_width/2
    
    if abs(denominator) < 1e-6:
        logging.warning("Denominator too small for b-value calculation, adjusting completeness magnitude")
        completeness_mag = completeness_mag - 0.1
        complete_mags = magnitudes[magnitudes >= completeness_mag]
        if len(complete_mags) <= 1:
            return np.nan
        mean_mag = np.mean(complete_mags)
        denominator = mean_mag - completeness_mag + bin_width/2
    
    b_value = log10(e) / denominator
    return b_value

def identify_aftershocks_optimized(df, cluster_radius, cluster_time):
    """Optimized aftershock identification using vectorized operations"""
    logging.info("Starting optimized aftershock identification...")
    
    # Get mainshocks (M >= 4.0)
    mainshocks = df[df['magnitude'] >= 4.0].copy().reset_index(drop=True)
    logging.info(f"Found {len(mainshocks)} potential mainshocks")
    
    if len(mainshocks) == 0:
        return pd.DataFrame(columns=['mainshock_id', 'aftershock_id', 'distance_km', 'time_diff_hours', 'mag_diff'])
    
    aftershocks = []
    
    # Convert time window to timedelta
    time_window = timedelta(hours=cluster_time)
    
    for idx, mainshock in mainshocks.iterrows():
        # Time filtering first (most selective)
        time_mask = (df['datetime'] > mainshock['datetime']) & \
                   (df['datetime'] <= mainshock['datetime'] + time_window)
        candidates = df[time_mask]
        
        if len(candidates) == 0:
            continue
            
        # Vectorized distance calculation
        distances = haversine_vectorized(
            mainshock['latitude'], mainshock['longitude'],
            candidates['latitude'].values, candidates['longitude'].values
        )
        
        # Find events within spatial radius
        spatial_mask = distances <= cluster_radius
        nearby_events = candidates[spatial_mask]
        nearby_distances = distances[spatial_mask]
        
        if len(nearby_events) == 0:
            continue
            
        # Calculate time differences in hours
        time_diffs = (nearby_events['datetime'] - mainshock['datetime']).dt.total_seconds() / 3600
        mag_diffs = mainshock['magnitude'] - nearby_events['magnitude']
        
        # Create aftershock records
        for i, (_, aftershock) in enumerate(nearby_events.iterrows()):
            aftershocks.append({
                'mainshock_id': mainshock['event_id'],
                'aftershock_id': aftershock['event_id'],
                'distance_km': float(nearby_distances[i]),
                'time_diff_hours': float(time_diffs.iloc[i]),
                'mag_diff': float(mag_diffs.iloc[i])
            })
    
    logging.info(f"Identified {len(aftershocks)} aftershock associations")
    return pd.DataFrame(aftershocks)

def compute_magnitude_frequency(magnitudes, bin_width=0.1):
    """Compute magnitude-frequency statistics"""
    min_mag = np.floor(magnitudes.min() * 10) / 10
    max_mag = np.ceil(magnitudes.max() * 10) / 10
    n_bins = int((max_mag - min_mag) / bin_width) + 1
    bins = np.linspace(min_mag, max_mag, n_bins + 1)
    
    hist, bin_edges = np.histogram(magnitudes, bins=bins)
    
    mag_freq = []
    cumulative = 0
    for i in range(len(hist)-1, -1, -1):
        cumulative += hist[i]
        mag_freq.append({
            'mag_bin': round(bin_edges[i], 1),
            'count': int(hist[i]),
            'cumulative_count': int(cumulative),
            'log10_cumulative': log10(cumulative) if cumulative > 0 else 0
        })
    
    mag_freq.reverse()
    return pd.DataFrame(mag_freq)

def to_json_serializable(obj):
    """Convert numpy/pandas types to JSON serializable types"""
    if isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif pd.isna(obj):
        return None
    else:
        return obj

def load_earthquake_data(filepath):
    """Load earthquake catalog from CSV"""
    df = pd.read_csv(filepath)
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    return df

def main():
    parser = argparse.ArgumentParser(description='Analyze earthquake catalog and identify aftershock sequences')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--cluster-radius', type=float, default=50.0, help='Clustering radius in km (default: 50)')
    parser.add_argument('--cluster-time', type=float, default=72.0, help='Clustering time window in hours (default: 72)')
    
    args = parser.parse_args()
    
    setup_logging()
    logging.info("Starting earthquake catalog analysis")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    df = load_earthquake_data(args.input)
    logging.info(f"Loaded {len(df)} earthquake events")
    
    # Calculate basic statistics
    completeness_mag = estimate_completeness_magnitude(df['magnitude'])
    b_value = calculate_b_value(df['magnitude'], completeness_mag)
    
    largest_event = df.loc[df['magnitude'].idxmax()]
    
    # Identify aftershock sequences (optimized version)
    aftershock_df = identify_aftershocks_optimized(df, args.cluster_radius, args.cluster_time)
    
    # Compute magnitude-frequency statistics
    mag_freq_df = compute_magnitude_frequency(df['magnitude'])
    
    # Save outputs with proper type conversion
    catalog_stats = {
        'b_value': to_json_serializable(b_value) if not np.isnan(b_value) else None,
        'completeness_mag': to_json_serializable(completeness_mag),
        'largest_event': {
            'id': to_json_serializable(largest_event['event_id']),
            'mag': to_json_serializable(largest_event['magnitude']),
            'lat': to_json_serializable(largest_event['latitude']),
            'lon': to_json_serializable(largest_event['longitude']),
            'depth': to_json_serializable(largest_event['depth_km'])
        },
        'total_events': len(df),
        'aftershock_count': len(aftershock_df)
    }
    
    with open(os.path.join(args.output, 'catalog_stats.json'), 'w') as f:
        json.dump(catalog_stats, f, indent=2)
    
    aftershock_df.to_csv(os.path.join(args.output, 'aftershock_sequences.csv'), index=False)
    mag_freq_df.to_csv(os.path.join(args.output, 'magnitude_freq.csv'), index=False)
    
    # Print summary
    print(f"Total events: {len(df)}")
    print(f"B-value: {b_value:.3f}" if not np.isnan(b_value) else "B-value: Unable to calculate")
    print(f"Number of aftershock sequences: {len(aftershock_df)}")
    print(f"Largest event: M{largest_event['magnitude']:.1f}")

if __name__ == "__main__":
    main()
