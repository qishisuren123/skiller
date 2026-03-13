import argparse
import pandas as pd
import numpy as np
import json
import os
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in km"""
    R = 6371.0  # Earth's radius in kilometers
    
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    return R * c

def estimate_magnitude_completeness(magnitudes, bin_width=0.1):
    """Estimate magnitude of completeness from frequency-magnitude distribution"""
    if len(magnitudes) == 0:
        return np.nan
    
    # Create magnitude bins
    min_mag = np.floor(magnitudes.min() / bin_width) * bin_width
    max_mag = np.ceil(magnitudes.max() / bin_width) * bin_width
    bins = np.arange(min_mag, max_mag + bin_width, bin_width)
    
    # Calculate histogram
    hist, bin_edges = np.histogram(magnitudes, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Find magnitude of completeness as the magnitude with maximum frequency
    if len(hist) == 0 or hist.max() == 0:
        return magnitudes.min()
    
    max_freq_idx = np.argmax(hist)
    return bin_centers[max_freq_idx]

def compute_b_value(magnitudes, completeness_mag, delta_bin=0.1):
    """Compute Gutenberg-Richter b-value using Aki's maximum likelihood formula"""
    complete_mags = magnitudes[magnitudes >= completeness_mag]
    
    if len(complete_mags) == 0:
        return np.nan
    
    mean_mag = np.mean(complete_mags)
    
    # Aki's formula: b = log10(e) / (mean_mag - completeness_mag + delta_bin/2)
    b_value = np.log10(np.e) / (mean_mag - completeness_mag + delta_bin/2)
    
    return b_value

def identify_aftershock_sequences(df, cluster_radius_km, cluster_time_hours):
    """Identify aftershock sequences based on spatial-temporal clustering"""
    sequences = []
    
    # Sort by datetime to ensure proper temporal ordering
    df_sorted = df.sort_values('datetime').reset_index(drop=True)
    
    # Find mainshocks (magnitude >= 4.0)
    mainshocks = df_sorted[df_sorted['magnitude'] >= 4.0].copy()
    
    for _, mainshock in mainshocks.iterrows():
        mainshock_time = mainshock['datetime']
        mainshock_lat = mainshock['latitude']
        mainshock_lon = mainshock['longitude']
        mainshock_id = mainshock['event_id']
        
        # Find potential aftershocks (events after mainshock within time window)
        time_mask = (df_sorted['datetime'] > mainshock_time) & \
                   (df_sorted['datetime'] <= mainshock_time + timedelta(hours=cluster_time_hours))
        
        potential_aftershocks = df_sorted[time_mask].copy()
        
        for _, aftershock in potential_aftershocks.iterrows():
            # Calculate distance
            distance = haversine_distance(
                mainshock_lat, mainshock_lon,
                aftershock['latitude'], aftershock['longitude']
            )
            
            if distance <= cluster_radius_km:
                time_diff = (aftershock['datetime'] - mainshock_time).total_seconds() / 3600  # hours
                mag_diff = aftershock['magnitude'] - mainshock['magnitude']
                
                sequences.append({
                    'mainshock_id': mainshock_id,
                    'aftershock_id': aftershock['event_id'],
                    'distance_km': distance,
                    'time_diff_hours': time_diff,
                    'mag_diff': mag_diff
                })
    
    return pd.DataFrame(sequences)

def compute_magnitude_frequency(magnitudes, bin_width=0.1):
    """Compute magnitude-frequency statistics"""
    if len(magnitudes) == 0:
        return pd.DataFrame()
    
    # Create magnitude bins
    min_mag = np.floor(magnitudes.min() / bin_width) * bin_width
    max_mag = np.ceil(magnitudes.max() / bin_width) * bin_width
    bins = np.arange(min_mag, max_mag + bin_width, bin_width)
    
    # Calculate histogram
    hist, bin_edges = np.histogram(magnitudes, bins=bins)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Calculate cumulative counts (from high to low magnitude)
    cumulative_count = np.cumsum(hist[::-1])[::-1]
    
    # Create DataFrame
    mag_freq_df = pd.DataFrame({
        'mag_bin': bin_centers,
        'count': hist,
        'cumulative_count': cumulative_count,
        'log10_cumulative': np.log10(np.maximum(cumulative_count, 1))  # Avoid log(0)
    })
    
    return mag_freq_df

def main():
    parser = argparse.ArgumentParser(description='Analyze earthquake catalog for aftershock sequences')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--cluster-radius', type=float, default=50.0, 
                       help='Clustering radius in km (default: 50)')
    parser.add_argument('--cluster-time', type=float, default=72.0,
                       help='Clustering time window in hours (default: 72)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    try:
        # Load earthquake catalog
        print(f"Loading earthquake catalog from {args.input}...")
        df = pd.read_csv(args.input)
        
        # Validate required columns
        required_columns = ['event_id', 'datetime', 'latitude', 'longitude', 'depth_km', 'magnitude', 'mag_type']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Parse datetime
        df['datetime'] = pd.to_datetime(df['datetime'])
        
        # Validate coordinate ranges
        if not df['latitude'].between(-90, 90).all():
            raise ValueError("Invalid latitude values found (must be between -90 and 90)")
        if not df['longitude'].between(-180, 180).all():
            raise ValueError("Invalid longitude values found (must be between -180 and 180)")
        
        print(f"Loaded {len(df)} earthquake events")
        
        # Estimate magnitude of completeness and compute b-value
        print("Computing Gutenberg-Richter b-value...")
        completeness_mag = estimate_magnitude_completeness(df['magnitude'])
        b_value = compute_b_value(df['magnitude'], completeness_mag)
        
        # Find largest event
        largest_event_idx = df['magnitude'].idxmax()
        largest_event = df.loc[largest_event_idx]
        
        # Identify aftershock sequences
        print("Identifying aftershock sequences...")
        sequences_df = identify_aftershock_sequences(df, args.cluster_radius, args.cluster_time)
        
        # Compute magnitude-frequency statistics
        print("Computing magnitude-frequency statistics...")
        mag_freq_df = compute_magnitude_frequency(df['magnitude'])
        
        # Prepare catalog statistics
        catalog_stats = {
            'b_value': float(b_value) if not np.isnan(b_value) else None,
            'completeness_mag': float(completeness_mag) if not np.isnan(completeness_mag) else None,
            'largest_event': {
                'id': str(largest_event['event_id']),
                'mag': float(largest_event['magnitude']),
                'lat': float(largest_event['latitude']),
                'lon': float(largest_event['longitude']),
                'depth': float(largest_event['depth_km'])
            },
            'total_events': int(len(df))
        }
        
        # Save outputs
        print("Saving results...")
        
        # Save catalog statistics
        with open(os.path.join(args.output, 'catalog_stats.json'), 'w') as f:
            json.dump(catalog_stats, f, indent=2)
        
        # Save aftershock sequences
        sequences_df.to_csv(os.path.join(args.output, 'aftershock_sequences.csv'), index=False)
        
        # Save magnitude-frequency data
        mag_freq_df.to_csv(os.path.join(args.output, 'magnitude_freq.csv'), index=False)
        
        # Print summary
        print("\n" + "="*50)
        print("EARTHQUAKE CATALOG ANALYSIS SUMMARY")
        print("="*50)
        print(f"Total events: {len(df)}")
        print(f"Magnitude of completeness: {completeness_mag:.2f}")
        print(f"Gutenberg-Richter b-value: {b_value:.3f}")
        print(f"Number of aftershock sequences identified: {len(sequences_df)}")
        print(f"Largest event: M{largest_event['magnitude']:.1f} at {largest_event['latitude']:.3f}°N, {largest_event['longitude']:.3f}°E")
        print(f"Clustering parameters: {args.cluster_radius} km, {args.cluster_time} hours")
        print(f"Results saved to: {args.output}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
