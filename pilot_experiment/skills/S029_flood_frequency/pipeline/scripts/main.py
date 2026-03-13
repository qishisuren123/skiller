#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
from scipy import stats
import json
import os
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze streamflow records and perform flood frequency analysis')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--return-periods', default='10,50,100', 
                       help='Comma-separated return periods in years (default: 10,50,100)')
    return parser.parse_args()

def load_data(input_file):
    """Load and validate streamflow data"""
    df = pd.read_csv(input_file)
    df['date'] = pd.to_datetime(df['date'])
    return df

def extract_annual_maxima(df, water_year=True):
    """Extract annual maximum discharge for each station"""
    annual_maxima = []
    
    for station in df['station_id'].unique():
        station_data = df[df['station_id'] == station].copy()
        station_data = station_data.sort_values('date')
        
        if water_year:
            # Water year: Oct 1 - Sep 30 (corrected logic)
            station_data['water_year'] = station_data['date'].dt.year
            # If month is Oct, Nov, Dec (10, 11, 12), it belongs to next water year
            mask = station_data['date'].dt.month >= 10
            station_data.loc[mask, 'water_year'] = station_data.loc[mask, 'date'].dt.year + 1
            year_col = 'water_year'
        else:
            station_data['calendar_year'] = station_data['date'].dt.year
            year_col = 'calendar_year'
        
        yearly_max = station_data.groupby(year_col)['discharge_cms'].max().reset_index()
        yearly_max['station_id'] = station
        yearly_max.rename(columns={year_col: 'year', 'discharge_cms': 'max_discharge'}, inplace=True)
        annual_maxima.append(yearly_max)
    
    return pd.concat(annual_maxima, ignore_index=True)

def baseflow_separation(df, alpha=0.925):
    """Perform baseflow separation using digital filter"""
    baseflow_results = []
    
    for station in df['station_id'].unique():
        station_data = df[df['station_id'] == station].copy()
        station_data = station_data.sort_values('date').reset_index(drop=True)
        
        Q = station_data['discharge_cms'].values
        
        # Handle missing data - mark invalid values
        valid_mask = ~np.isnan(Q) & (Q >= 0)
        if not np.any(valid_mask):
            print(f"Warning: No valid data for station {station}")
            continue
            
        baseflow = np.full_like(Q, np.nan)
        
        # Find continuous segments of valid data
        valid_indices = np.where(valid_mask)[0]
        
        if len(valid_indices) == 0:
            continue
            
        # Process each continuous segment separately
        segment_starts = [valid_indices[0]]
        for i in range(1, len(valid_indices)):
            if valid_indices[i] - valid_indices[i-1] > 1:  # Gap detected
                segment_starts.append(valid_indices[i])
        
        # Process each continuous segment
        for start_idx in segment_starts:
            # Find end of this segment
            segment_indices = []
            for idx in valid_indices:
                if idx >= start_idx:
                    if not segment_indices or idx - segment_indices[-1] <= 1:
                        segment_indices.append(idx)
                    else:
                        break
            
            if len(segment_indices) < 2:
                continue  # Need at least 2 points for the filter
                
            # Initialize first value of segment
            baseflow[segment_indices[0]] = Q[segment_indices[0]]
            
            # Apply filter within this continuous segment
            for i in range(1, len(segment_indices)):
                t = segment_indices[i]
                t_prev = segment_indices[i-1]
                
                # Calculate filter value
                filter_value = alpha * baseflow[t_prev] + (1-alpha)/2 * (Q[t] + Q[t_prev])
                
                # Apply clipping constraint
                baseflow[t] = min(filter_value, Q[t])
        
        # Calculate quickflow (will be NaN where baseflow is NaN)
        quickflow = Q - baseflow
        
        # Add results to dataframe
        result_df = station_data[['date', 'station_id', 'discharge_cms']].copy()
        result_df['baseflow_cms'] = baseflow
        result_df['quickflow_cms'] = quickflow
        
        baseflow_results.append(result_df)
    
    return pd.concat(baseflow_results, ignore_index=True)

def fit_gev_and_calculate_floods(annual_max, return_periods):
    """Fit GEV distribution and calculate flood discharges for return periods"""
    flood_results = {}
    
    for station in annual_max['station_id'].unique():
        station_max = annual_max[annual_max['station_id'] == station]['max_discharge'].values
        
        if len(station_max) < 3:
            print(f"Warning: Station {station} has insufficient data ({len(station_max)} years)")
            continue
        
        # Data validation and preprocessing
        station_max = station_max[~np.isnan(station_max)]
        station_max = station_max[station_max > 0]
        
        if len(station_max) < 3:
            print(f"Warning: Station {station} has insufficient valid data after cleaning")
            continue
        
        # Calculate basic statistics for validation
        max_observed = np.max(station_max)
        mean_observed = np.mean(station_max)
        
        try:
            # Fit GEV distribution
            shape, loc, scale = stats.genextreme.fit(station_max, method='MLE')
            
            if scale <= 0:
                raise ValueError("Invalid scale parameter")
            
            # Check if shape parameter is reasonable
            if shape < -0.5:
                print(f"Warning: Station {station} has very negative shape parameter ({shape:.3f})")
                
        except Exception as e:
            print(f"Warning: GEV fitting failed for station {station}: {e}")
            try:
                # Try method of moments as fallback
                shape, loc, scale = stats.genextreme.fit(station_max, method='MM')
                if scale <= 0:
                    raise ValueError("Method of moments also failed")
            except:
                print(f"  All fitting methods failed for station {station}, skipping...")
                continue
        
        # Calculate flood discharges with validation
        return_period_floods = {}
        for T in return_periods:
            try:
                prob = 1 - 1/T
                Q_T = stats.genextreme.ppf(prob, shape, loc=loc, scale=scale)
                
                if not np.isfinite(Q_T) or Q_T <= 0:
                    print(f"Warning: Invalid flood estimate for station {station}, return period {T}")
                    continue
                
                # Sanity check: flood estimate vs observed data
                ratio_to_max = Q_T / max_observed
                
                if ratio_to_max > 5.0:  # More than 5x the maximum observed
                    print(f"Warning: Station {station}, {T}-year flood ({Q_T:.1f}) is {ratio_to_max:.1f}x max observed ({max_observed:.1f})")
                    print(f"  GEV params: shape={shape:.3f}, loc={loc:.1f}, scale={scale:.1f}")
                    
                return_period_floods[T] = float(Q_T)
            except Exception as e:
                print(f"Warning: Failed to calculate {T}-year flood for station {station}: {e}")
        
        if return_period_floods:  # Only add if we have valid results
            flood_results[station] = {
                'gev_params': {
                    'shape': float(shape),
                    'loc': float(loc), 
                    'scale': float(scale)
                },
                'return_periods': return_period_floods
            }
    
    return flood_results

def main():
    args = parse_arguments()
    
    # Parse return periods
    return_periods = [int(x.strip()) for x in args.return_periods.split(',')]
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    df = load_data(args.input)
    
    # Extract annual maxima
    annual_max = extract_annual_maxima(df)
    
    # Fit GEV and calculate floods
    flood_results = fit_gev_and_calculate_floods(annual_max, return_periods)
    
    # Perform baseflow separation
    baseflow_df = baseflow_separation(df)
    
    # Save results
    annual_max.to_csv(os.path.join(args.output, 'annual_maxima.csv'), index=False)
    
    with open(os.path.join(args.output, 'flood_frequency.json'), 'w') as f:
        json.dump(flood_results, f, indent=2)
    
    baseflow_df.to_csv(os.path.join(args.output, 'baseflow.csv'), index=False)
    
    # Print summary
    print(f"Processed {len(annual_max['station_id'].unique())} stations")
    print(f"Years of record: {annual_max['year'].min()}-{annual_max['year'].max()}")
    
    for station, results in flood_results.items():
        q100 = results['return_periods'].get(100, 'N/A')
        print(f"Station {station}: 100-year flood = {q100:.1f} cms")

if __name__ == '__main__':
    main()
