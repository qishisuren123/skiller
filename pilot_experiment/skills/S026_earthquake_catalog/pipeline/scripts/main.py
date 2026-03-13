#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from datetime import datetime, timedelta
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance between two points on Earth in kilometers"""
    R = 6371  # Earth's radius in kilometers
    
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def calculate_b_value(magnitudes):
    """Calculate Gutenberg-Richter b-value using Aki formula with better completeness estimation"""
    # Create magnitude-frequency histogram
    mag_bins = np.arange(math.floor(min(magnitudes)*10)/10, 
                        math.ceil(max(magnitudes)*10)/10 + 0.1, 0.1)
    hist, _ = np.histogram(magnitudes, bins=mag_bins)
    
    # Calculate reverse cumulative counts
    cumulative = []
    for i in range(len(hist)):
        cum_count = np.sum(hist[i:])
        cumulative.append(cum_count)
    
    # Find completeness magnitude using maximum curvature method
    completeness_mag = None
    best_r_squared = -1
    
    # Try different potential completeness magnitudes
    for i in range(len(mag_bins)-3):  # Need at least 3 points for regression
        test_mag = mag_bins[i]
        
        # Get data points >= test magnitude with non-zero counts
        valid_indices = []
        for j in range(i, len(cumulative)):
            if cumulative[j] > 0:
                valid_indices.append(j)
        
        if len(valid_indices) < 3:  # Need at least 3 points
            continue
            
        # Perform linear regression on log10(cumulative) vs magnitude
        x_vals = [mag_bins[j] for j in valid_indices]
        y_vals = [math.log10(cumulative[j]) for j in valid_indices]
        
        if len(x_vals) < 3:
            continue
            
        # Calculate R-squared for linear fit
        x_mean = np.mean(x_vals)
        y_mean = np.mean(y_vals)
        
        # Check for zero variance in x (all x values the same)
        x_variance = sum((x - x_mean)**2 for x in x_vals)
        if x_variance == 0:
            continue
            
        ss_tot = sum((y - y_mean)**2 for y in y_vals)
        if ss_tot == 0:
            continue
            
        # Calculate slope and intercept
        slope = sum((x_vals[k] - x_mean) * (y_vals[k] - y_mean) for k in range(len(x_vals))) / x_variance
        
        y_pred = [slope * (x - x_mean) + y_mean for x in x_vals]
        ss_res = sum((y_vals[k] - y_pred[k])**2 for k in range(len(y_vals)))
        
        r_squared = 1 - (ss_res / ss_tot)
        
        # Choose the magnitude with best linear fit (highest R²)
        if r_squared > best_r_squared and r_squared > 0.9:  # Require good fit
            best_r_squared = r_squared
            completeness_mag = test_mag
    
    # Fallback to maximum of histogram if no good linear fit found
    if completeness_mag is None:
        completeness_mag = mag_bins[np.argmax(hist)]
    
    # Filter magnitudes >= completeness magnitude
    complete_mags = [m for m in magnitudes if m >= completeness_mag]
    
    if len(complete_mags) < 2:
        return None, completeness_mag
    
    mean_mag = np.mean(complete_mags)
    min_mag = min(complete_mags)
    delta_bin = 0.1
    
    # Check for division by zero
    denominator = mean_mag - min_mag + delta_bin/2
    if denominator <= 0:
        return None, completeness_mag
    
    # Aki formula
    b_value = math.log10(math.e) / denominator
    
    return b_value, completeness_mag

def identify_aftershocks(df, cluster_radius, cluster_time):
    """Identify aftershock sequences - prevent events from being both mainshock and aftershock"""
    aftershocks = []
    used_as_aftershock = set()  # Track events already classified as aftershocks
    
    # Find potential mainshocks (magnitude >= 4.0), sorted by magnitude (largest first)
    mainshocks = df[df['magnitude'] >= 4.0].copy().sort_values('magnitude', ascending=False)
    
    for _, mainshock in mainshocks.iterrows():
        # Skip if this event was already classified as an aftershock
        if mainshock['event_id'] in used_as_aftershock:
            continue
            
        mainshock_time = mainshock['datetime']
        mainshock_lat = mainshock['latitude']
        mainshock_lon = mainshock['longitude']
        
        # Find events after this mainshock within time window
        time_mask = (df['datetime'] > mainshock_time) & \
                   (df['datetime'] <= mainshock_time + timedelta(hours=cluster_time))
        candidates = df[time_mask]
        
        for _, candidate in candidates.iterrows():
            # Skip if already classified as aftershock
            if candidate['event_id'] in used_as_aftershock:
                continue
                
            # Calculate distance
            distance = haversine_distance(
                mainshock_lat, mainshock_lon,
                candidate['latitude'], candidate['longitude']
            )
            
            if distance <= cluster_radius:
                time_diff = (candidate['datetime'] - mainshock_time).total_seconds() / 3600
                mag_diff = candidate['magnitude'] - mainshock['magnitude']
                
                aftershocks.append({
                    'mainshock_id': mainshock['event_id'],
                    'aftershock_id': candidate['event_id'],
                    'distance_km': distance,
                    'time_diff_hours': time_diff,
                    'mag_diff': mag_diff
                })
                
                # Mark this event as used
                used_as_aftershock.add(candidate['event_id'])
    
    return pd.DataFrame(aftershocks)

def calculate_magnitude_frequency(magnitudes):
    """Calculate magnitude-frequency statistics"""
    mag_bins = np.arange(math.floor(min(magnitudes)*10)/10, 
                        math.ceil(max(magnitudes)*10)/10 + 0.1, 0.1)
    hist, _ = np.histogram(magnitudes, bins=mag_bins)
    
    # Calculate reverse cumulative counts correctly
    # Each bin should contain count of events >= that magnitude
    cumulative = []
    for i in range(len(hist)):
        cum_count = np.sum(hist[i:])  # Sum from current bin to end
        cumulative.append(cum_count)
    
    mag_freq_data = []
    for i, mag_bin in enumerate(mag_bins[:-1]):
        count = hist[i]
        cum_count = cumulative[i]
        log10_cum = math.log10(cum_count) if cum_count > 0 else None
        
        mag_freq_data.append({
            'mag_bin': round(mag_bin, 1),
            'count': count,
            'cumulative_count': cum_count,
            'log10_cumulative': log10_cum
        })
    
    return pd.DataFrame(mag_freq_data)

def validate_input_columns(df):
    """Validate that required columns exist in the dataframe"""
    required_columns = ['event_id', 'latitude', 'longitude', 'depth_km', 'magnitude']
    missing_columns = []
    
    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    # Check for datetime column variants
    datetime_col = None
    for col in ['datetime', 'date_time', 'time', 'origin_time']:
        if col in df.columns:
            datetime_col = col
            break
    
    if datetime_col is None:
        missing_columns.append('datetime (or date_time, time, origin_time)')
    
    return missing_columns, datetime_col

def main():
    parser = argparse.ArgumentParser(description='Analyze earthquake catalog and identify aftershock sequences')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--cluster-radius', type=float, default=50.0, help='Clustering radius in km (default: 50)')
    parser.add_argument('--cluster-time', type=float, default=72.0, help='Clustering time window in hours (default: 72)')
    
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    os.makedirs(args.output, exist_ok=True)
    
    # Load earthquake catalog
    try:
        df = pd.read_csv(args.input)
        
        # Validate columns
        missing_columns, datetime_col = validate_input_columns(df)
        if missing_columns:
            print(f"Error: Missing required columns: {', '.join(missing_columns)}")
            return
            
        df['datetime'] = pd.to_datetime(df[datetime_col])
        df = df.sort_values('datetime')
        
    except Exception as e:
        print(f"Error loading input file: {e}")
        return
    
    print(f"Loaded {len(df)} events from {args.input}")
    
    # Calculate b-value
    b_value, completeness_mag = calculate_b_value(df['magnitude'].values)
    
    # Find largest event
    largest_event = df.loc[df['magnitude'].idxmax()]
    
    # Identify aftershock sequences
    aftershock_df = identify_aftershocks(df, args.cluster_radius, args.cluster_time)
    
    # Calculate magnitude-frequency statistics
    mag_freq_df = calculate_magnitude_frequency(df['magnitude'].values)
    
    # Write outputs
    # 1. Catalog stats JSON
    catalog_stats = {
        'b_value': b_value,
        'completeness_mag': completeness_mag,
        'largest_event': {
            'id': largest_event['event_id'],
            'mag': largest_event['magnitude'],
            'lat': largest_event['latitude'],
            'lon': largest_event['longitude'],
            'depth': largest_event['depth_km']
        },
        'total_events': len(df)
    }
    
    with open(os.path.join(args.output, 'catalog_stats.json'), 'w') as f:
        json.dump(catalog_stats, f, indent=2)
    
    # 2. Aftershock sequences CSV
    aftershock_df.to_csv(os.path.join(args.output, 'aftershock_sequences.csv'), index=False)
    
    # 3. Magnitude frequency CSV
    mag_freq_df.to_csv(os.path.join(args.output, 'magnitude_freq.csv'), index=False)
    
    # Print summary
    print(f"Analysis complete!")
    print(f"Total events: {len(df)}")
    print(f"B-value: {b_value:.3f}" if b_value else "B-value: Could not calculate")
    print(f"Number of aftershock sequences: {len(aftershock_df)}")
    print(f"Largest event: M{largest_event['magnitude']:.1f}")
    print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()
