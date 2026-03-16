#!/usr/bin/env python3
"""
Heat Index Analysis and Heat Wave Detection CLI Tool
"""

import argparse
import pandas as pd
import numpy as np
import json
import logging
from datetime import datetime, timedelta
from scipy import stats
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def calculate_heat_index(temp_f, humidity):
    """
    Calculate heat index using the full National Weather Service formula
    
    Args:
        temp_f: Temperature in Fahrenheit
        humidity: Relative humidity (0-100)
    
    Returns:
        Heat index in Fahrenheit
    """
    # Convert to numpy arrays for vectorized operations
    T = np.asarray(temp_f)
    RH = np.asarray(humidity)
    
    # Initialize heat index array
    HI = np.full_like(T, np.nan, dtype=float)
    
    # For temperatures below 80°F, heat index equals air temperature
    mask_low = T < 80
    HI[mask_low] = T[mask_low]
    
    # For temperatures 80°F and above, use the full NWS formula
    mask_high = T >= 80
    
    if np.any(mask_high):
        T_high = T[mask_high]
        RH_high = RH[mask_high]
        
        # Full NWS heat index formula coefficients
        c1 = -42.379
        c2 = 2.04901523
        c3 = 10.14333127
        c4 = -0.22475541
        c5 = -6.83783e-3
        c6 = -5.481717e-2
        c7 = 1.22874e-3
        c8 = 8.5282e-4
        c9 = -1.99e-6
        
        # Calculate base heat index
        HI_calc = (c1 + c2*T_high + c3*RH_high + c4*T_high*RH_high + 
                   c5*T_high**2 + c6*RH_high**2 + c7*T_high**2*RH_high + 
                   c8*T_high*RH_high**2 + c9*T_high**2*RH_high**2)
        
        # Apply adjustments for low humidity
        low_rh_mask = (RH_high < 13) & (T_high >= 80) & (T_high <= 112)
        if np.any(low_rh_mask):
            adjustment = ((13 - RH_high[low_rh_mask])/4) * np.sqrt((17 - np.abs(T_high[low_rh_mask] - 95))/17)
            HI_calc[low_rh_mask] -= adjustment
        
        # Apply adjustments for high humidity
        high_rh_mask = (RH_high > 85) & (T_high >= 80) & (T_high <= 87)
        if np.any(high_rh_mask):
            adjustment = ((RH_high[high_rh_mask] - 85)/10) * ((87 - T_high[high_rh_mask])/5)
            HI_calc[high_rh_mask] += adjustment
        
        HI[mask_high] = HI_calc
    
    return HI

def load_and_merge_data(temp_file, humidity_file):
    """Load temperature and humidity data and merge on datetime"""
    logger.info(f"Loading temperature data from {temp_file}")
    temp_df = pd.read_csv(temp_file)
    
    # Check and standardize column names for temperature data
    if 'date' in temp_df.columns:
        temp_df['datetime'] = pd.to_datetime(temp_df['date'])
    elif 'datetime' in temp_df.columns:
        temp_df['datetime'] = pd.to_datetime(temp_df['datetime'])
    else:
        raise ValueError("Temperature file must contain 'date' or 'datetime' column")
    
    if 'temp_f' in temp_df.columns:
        temp_df['temperature'] = temp_df['temp_f']
    elif 'temperature' in temp_df.columns:
        pass  # Already correct
    else:
        raise ValueError("Temperature file must contain 'temp_f' or 'temperature' column")
    
    logger.info(f"Loading humidity data from {humidity_file}")
    humidity_df = pd.read_csv(humidity_file)
    
    # Check and standardize column names for humidity data
    if 'date' in humidity_df.columns:
        humidity_df['datetime'] = pd.to_datetime(humidity_df['date'])
    elif 'datetime' in humidity_df.columns:
        humidity_df['datetime'] = pd.to_datetime(humidity_df['datetime'])
    else:
        raise ValueError("Humidity file must contain 'date' or 'datetime' column")
    
    if 'rh_percent' in humidity_df.columns:
        humidity_df['humidity'] = humidity_df['rh_percent']
    elif 'humidity' in humidity_df.columns:
        pass  # Already correct
    else:
        raise ValueError("Humidity file must contain 'rh_percent' or 'humidity' column")
    
    # Select only needed columns for merge
    temp_clean = temp_df[['datetime', 'temperature']]
    humidity_clean = humidity_df[['datetime', 'humidity']]
    
    # Merge datasets
    merged_df = pd.merge(temp_clean, humidity_clean, on='datetime', how='inner')
    merged_df = merged_df.sort_values('datetime').reset_index(drop=True)
    
    logger.info(f"Merged dataset contains {len(merged_df)} records")
    return merged_df

def calculate_climatological_baseline(data, baseline_years, percentile_threshold):
    """Calculate climatological baseline using rolling window approach"""
    logger.info(f"Calculating {baseline_years}-year climatological baseline...")
    
    data = data.copy()
    data['date'] = pd.to_datetime(data['datetime']).dt.date
    data['day_of_year'] = pd.to_datetime(data['datetime']).dt.dayofyear
    data['year'] = pd.to_datetime(data['datetime']).dt.year
    
    # Get daily maximum heat index
    daily_max = data.groupby('date').agg({
        'heat_index': 'max',
        'day_of_year': 'first',
        'year': 'first',
        'datetime': 'first'
    }).reset_index()
    
    # Calculate baseline thresholds for each day of year
    baseline_thresholds = {}
    
    for doy in range(1, 367):  # Include leap day
        # Get 15-day window around this day of year
        window_days = []
        for offset in range(-7, 8):  # 15-day window
            target_doy = doy + offset
            if target_doy < 1:
                target_doy += 365
            elif target_doy > 365:
                target_doy -= 365
            window_days.append(target_doy)
        
        # Get historical data for this window
        window_data = daily_max[daily_max['day_of_year'].isin(window_days)]
        
        # Use most recent baseline_years of data
        recent_years = sorted(window_data['year'].unique())[-baseline_years:]
        baseline_data = window_data[window_data['year'].isin(recent_years)]
        
        if len(baseline_data) > 0:
            threshold = np.percentile(baseline_data['heat_index'].dropna(), percentile_threshold)
            baseline_thresholds[doy] = threshold
        else:
            baseline_thresholds[doy] = np.nan
    
    # Add thresholds to daily data
    daily_max['threshold'] = daily_max['day_of_year'].map(baseline_thresholds)
    daily_max['exceeds_threshold'] = daily_max['heat_index'] > daily_max['threshold']
    
    return daily_max

def detect_heat_waves(daily_data, min_duration):
    """Detect heat wave events based on threshold exceedances"""
    logger.info(f"Detecting heat waves with minimum duration of {min_duration} days...")
    
    daily_data = daily_data.sort_values('date').reset_index(drop=True)
    heat_waves = []
    
    # Find consecutive periods above threshold
    in_heatwave = False
    current_event = []
    
    for idx, row in daily_data.iterrows():
        if row['exceeds_threshold'] and not pd.isna(row['heat_index']):
            if not in_heatwave:
                # Start new heat wave
                in_heatwave = True
                current_event = [idx]
            else:
                # Continue current heat wave
                current_event.append(idx)
        else:
            if in_heatwave:
                # End current heat wave
                if len(current_event) >= min_duration:
                    # Extract heat wave data
                    hw_data = daily_data.iloc[current_event]
                    heat_wave = {
                        'start_date': hw_data['date'].iloc[0].isoformat(),
                        'end_date': hw_data['date'].iloc[-1].isoformat(),
                        'duration': len(current_event),
                        'mean_heat_index': float(hw_data['heat_index'].mean()),
                        'max_heat_index': float(hw_data['heat_index'].max()),
                        'mean_threshold': float(hw_data['threshold'].mean()),
                        'cumulative_excess': float((hw_data['heat_index'] - hw_data['threshold']).sum())
                    }
                    heat_waves.append(heat_wave)
                
                in_heatwave = False
                current_event = []
    
    # Handle case where data ends during a heat wave
    if in_heatwave and len(current_event) >= min_duration:
        hw_data = daily_data.iloc[current_event]
        heat_wave = {
            'start_date': hw_data['date'].iloc[0].isoformat(),
            'end_date': hw_data['date'].iloc[-1].isoformat(),
            'duration': len(current_event),
            'mean_heat_index': float(hw_data['heat_index'].mean()),
            'max_heat_index': float(hw_data['heat_index'].max()),
            'mean_threshold': float(hw_data['threshold'].mean()),
            'cumulative_excess': float((hw_data['heat_index'] - hw_data['threshold']).sum())
        }
        heat_waves.append(heat_wave)
    
    logger.info(f"Detected {len(heat_waves)} heat wave events")
    return heat_waves

def main():
    parser = argparse.ArgumentParser(description='Heat Index Analysis and Heat Wave Detection')
    parser.add_argument('--temp-data', required=True, help='Path to temperature data file (CSV)')
    parser.add_argument('--humidity-data', required=True, help='Path to humidity data file (CSV)')
    parser.add_argument('--output-timeseries', required=True, help='Path for heat index time series output (CSV)')
    parser.add_argument('--output-heatwaves', required=True, help='Path for heat wave events output (JSON)')
    parser.add_argument('--baseline-years', type=int, default=30, help='Years for baseline climatology')
    parser.add_argument('--heatwave-threshold', type=float, default=90, help='Percentile threshold for heat waves')
    parser.add_argument('--min-duration', type=int, default=3, help='Minimum heat wave duration in days')
    
    args = parser.parse_args()
    
    try:
        # Load and merge data
        data = load_and_merge_data(args.temp_data, args.humidity_data)
        
        # Calculate heat index
        logger.info("Calculating heat index...")
        data['heat_index'] = calculate_heat_index(data['temperature'], data['humidity'])
        
        # Calculate climatological baseline
        daily_data = calculate_climatological_baseline(data, args.baseline_years, args.heatwave_threshold)
        
        # Detect heat waves
        heat_waves = detect_heat_waves(daily_data, args.min_duration)
        
        # Add thresholds to original data
        data['date'] = pd.to_datetime(data['datetime']).dt.date
        threshold_map = dict(zip(daily_data['date'], daily_data['threshold']))
        data['threshold'] = data['date'].map(threshold_map)
        
        # Save time series
        logger.info(f"Saving heat index time series to {args.output_timeseries}")
        output_cols = ['datetime', 'temperature', 'humidity', 'heat_index', 'threshold']
        data[output_cols].to_csv(args.output_timeseries, index=False)
        
        # Save heat wave events
        logger.info(f"Saving heat wave events to {args.output_heatwaves}")
        heat_wave_output = {
            'parameters': {
                'baseline_years': args.baseline_years,
                'percentile_threshold': args.heatwave_threshold,
                'min_duration': args.min_duration
            },
            'events': heat_waves,
            'summary': {
                'total_events': len(heat_waves),
                'total_heat_wave_days': sum(hw['duration'] for hw in heat_waves)
            }
        }
        
        with open(args.output_heatwaves, 'w') as f:
            json.dump(heat_wave_output, f, indent=2)
        
        logger.info("Heat wave analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        raise

if __name__ == "__main__":
    main()
