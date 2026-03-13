#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os

def validate_and_clean_data(df):
    """Validate and clean input data"""
    print(f"Original data: {len(df)} levels")
    
    # Check required columns
    required_cols = ['pressure', 'temperature', 'dewpoint', 'wind_speed', 'wind_direction', 'altitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Remove rows with missing critical data
    critical_cols = ['pressure', 'temperature', 'altitude']
    before_clean = len(df)
    df_clean = df.dropna(subset=critical_cols)
    after_clean = len(df_clean)
    
    if after_clean == 0:
        raise ValueError("No valid data remaining after removing rows with missing critical values")
    
    print(f"Removed {before_clean - after_clean} levels with missing critical data")
    print(f"Clean data: {after_clean} levels")
    
    df_clean = df_clean.sort_values('altitude').reset_index(drop=True)
    return df_clean

def calculate_lapse_rates(df):
    """Calculate environmental lapse rate between consecutive levels"""
    lapse_rates = []
    
    for i in range(len(df) - 1):
        t1, t2 = df.iloc[i]['temperature'], df.iloc[i+1]['temperature']
        alt1, alt2 = df.iloc[i]['altitude'], df.iloc[i+1]['altitude']
        
        if pd.isna(t1) or pd.isna(t2) or pd.isna(alt1) or pd.isna(alt2):
            lapse_rates.append(np.nan)
            continue
            
        alt_diff_km = (alt2 - alt1) / 1000
        if alt_diff_km > 0:
            lapse_rate = -(t2 - t1) / alt_diff_km
            lapse_rates.append(lapse_rate)
        else:
            lapse_rates.append(np.nan)
    
    lapse_rates.append(np.nan)
    df['lapse_rate'] = lapse_rates
    return df

def find_tropopause(df):
    """Find tropopause: lowest level above 5km where lapse rate < 2°C/km for 2km depth"""
    above_5km = df[df['altitude'] >= 5000].copy().reset_index(drop=True)
    
    for i in range(len(above_5km)):
        row = above_5km.iloc[i]
        current_lapse = row['lapse_rate']
        current_alt = row['altitude']
        
        if pd.isna(current_lapse) or current_lapse >= 2.0:
            continue
            
        # Check if we have at least 2km of data above this level
        upper_limit = current_alt + 2000
        levels_above = above_5km[above_5km['altitude'] > current_alt]
        
        if len(levels_above) == 0:
            continue
            
        max_alt_above = levels_above['altitude'].max()
        if max_alt_above < upper_limit:
            continue
            
        check_levels = above_5km[(above_5km['altitude'] >= current_alt) & 
                                (above_5km['altitude'] <= upper_limit)]
        
        valid_lapse_rates = [lr for lr in check_levels['lapse_rate'] if not pd.isna(lr)]
        
        if len(valid_lapse_rates) >= 2:
            if all(lr < 2.0 for lr in valid_lapse_rates):
                return current_alt, row['pressure']
    
    return None, None

def calculate_cape_cin(df):
    """Calculate CAPE and CIN using simple parcel method"""
    if len(df) == 0:
        return 0.0, 0.0
    
    # Find surface level with valid temperature and dewpoint
    surface = None
    for i in range(len(df)):
        row = df.iloc[i]
        if not (pd.isna(row['temperature']) or pd.isna(row['dewpoint'])):
            surface = row
            break
    
    if surface is None:
        print("WARNING: No valid surface data for CAPE calculation")
        return 0.0, 0.0
    
    parcel_temp = surface['temperature']
    parcel_dewpoint = surface['dewpoint']
    
    cape = 0.0
    cin = 0.0
    lcl_found = False
    lfc_found = False
    g = 9.81
    
    for i in range(1, len(df)):
        current_level = df.iloc[i]
        prev_level = df.iloc[i-1]
        
        if pd.isna(current_level['temperature']) or pd.isna(current_level['altitude']):
            continue
            
        dz = current_level['altitude'] - prev_level['altitude']
        if dz <= 0:
            continue
        
        if not lcl_found:
            new_parcel_temp = parcel_temp - 9.8 * (dz / 1000)
            new_parcel_dewpoint = parcel_dewpoint - 2.0 * (dz / 1000)
            
            if new_parcel_temp <= new_parcel_dewpoint:
                lcl_found = True
            
            parcel_temp = new_parcel_temp
            parcel_dewpoint = new_parcel_dewpoint
        else:
            parcel_temp -= 6.0 * (dz / 1000)
        
        if current_level['altitude'] > surface['altitude'] + 100:
            env_temp_k = current_level['temperature'] + 273.15
            parcel_temp_k = parcel_temp + 273.15
            
            buoyancy = g * (parcel_temp_k - env_temp_k) / env_temp_k * dz
            
            if parcel_temp > current_level['temperature']:
                if not lfc_found:
                    lfc_found = True
                cape += buoyancy
            elif not lfc_found:
                cin += abs(buoyancy)
    
    return cape, cin

def detect_inversions(df):
    """Detect temperature inversions"""
    inversions = []
    in_inversion = False
    inversion_base = None
    inversion_base_temp = None
    
    for i in range(1, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        
        if pd.isna(current['temperature']) or pd.isna(prev['temperature']):
            continue
        
        if current['temperature'] > prev['temperature']:
            if not in_inversion:
                in_inversion = True
                inversion_base = prev['altitude']
                inversion_base_temp = prev['temperature']
        else:
            if in_inversion:
                inversion_top = prev['altitude']
                inversion_top_temp = prev['temperature']
                strength = inversion_top_temp - inversion_base_temp
                
                inversions.append({
                    'base_altitude_m': float(inversion_base),
                    'top_altitude_m': float(inversion_top),
                    'strength_C': float(strength)
                })
                in_inversion = False
    
    if in_inversion:
        last_level = df.iloc[-1]
        strength = last_level['temperature'] - inversion_base_temp
        inversions.append({
            'base_altitude_m': float(inversion_base),
            'top_altitude_m': float(last_level['altitude']),
            'strength_C': float(strength)
        })
    
    return inversions

def main():
    parser = argparse.ArgumentParser(description='Analyze radiosonde atmospheric sounding data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()
    
    try:
        # Read and validate data
        df = pd.read_csv(args.input)
        df = validate_and_clean_data(df)
        df = calculate_lapse_rates(df)
        
        # Analysis
        tropo_height, tropo_pressure = find_tropopause(df)
        cape, cin = calculate_cape_cin(df)
        inversions = detect_inversions(df)
        
        # Surface parameters
        surface = df.iloc[0]
        surface_temp = surface['temperature']
        surface_dewpoint = surface['dewpoint']
        
        # Create summary
        summary = {
            'tropopause_height_m': float(tropo_height) if tropo_height is not None else None,
            'tropopause_pressure_hPa': float(tropo_pressure) if tropo_pressure is not None else None,
            'CAPE_J_kg': float(cape),
            'CIN_J_kg': float(cin),
            'inversions': inversions,
            'surface_temperature_C': float(surface_temp),
            'surface_dewpoint_C': float(surface_dewpoint)
        }
        
        # Print results
        print(f"Tropopause height: {tropo_height} m")
        print(f"Tropopause pressure: {tropo_pressure} hPa")
        print(f"CAPE: {cape:.1f} J/kg")
        print(f"CIN: {cin:.1f} J/kg")
        print(f"Number of inversions: {len(inversions)}")
        print(f"Surface temperature: {surface_temp:.1f}°C")
        print(f"Surface dewpoint: {surface_dewpoint:.1f}°C")
        
        # Save outputs
        os.makedirs(args.output, exist_ok=True)
        df.to_csv(os.path.join(args.output, 'processed_profile.csv'), index=False)
        
        with open(os.path.join(args.output, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\nOutputs saved to {args.output}/")
        print("- processed_profile.csv")
        print("- summary.json")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
