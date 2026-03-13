import argparse
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

def calculate_lapse_rates(df):
    """Calculate environmental lapse rates between consecutive levels."""
    lapse_rates = []
    for i in range(len(df) - 1):
        dt = df.iloc[i+1]['temperature'] - df.iloc[i]['temperature']
        dz = df.iloc[i+1]['altitude'] - df.iloc[i]['altitude']
        if dz > 0:
            lapse_rate = -dt / (dz / 1000)  # °C/km
        else:
            lapse_rate = np.nan
        lapse_rates.append(lapse_rate)
    lapse_rates.append(np.nan)  # Last level has no lapse rate
    return lapse_rates

def find_tropopause(df):
    """Find tropopause using WMO criteria: lapse rate < 2°C/km above 5km for 2km depth."""
    # Filter data above 5 km
    above_5km = df[df['altitude'] >= 5000].copy()
    if len(above_5km) < 3:
        return None, None
    
    for i, row in above_5km.iterrows():
        if pd.isna(row['lapse_rate']) or row['lapse_rate'] >= 2.0:
            continue
            
        # Check if lapse rate stays < 2°C/km for next 2 km
        check_alt = row['altitude'] + 2000
        higher_levels = above_5km[above_5km['altitude'] <= check_alt]
        
        if len(higher_levels) > 1:
            avg_lapse = higher_levels['lapse_rate'].mean()
            if avg_lapse < 2.0:
                return row['altitude'], row['pressure']
    
    return None, None

def calculate_cape_cin(df):
    """Calculate CAPE and CIN using simple parcel method."""
    if len(df) < 2:
        return 0.0, 0.0
    
    # Surface parcel properties
    surface = df.iloc[0]
    parcel_temp = surface['temperature']
    parcel_dewpoint = surface['dewpoint']
    
    # Constants
    g = 9.81  # m/s²
    dry_lapse = 9.8  # °C/km
    moist_lapse = 6.0  # °C/km (approximation)
    
    cape = 0.0
    cin = 0.0
    lcl_found = False
    lfc_found = False
    
    for i in range(1, len(df)):
        current_alt = df.iloc[i]['altitude']
        env_temp = df.iloc[i]['temperature']
        prev_alt = df.iloc[i-1]['altitude']
        
        dz = current_alt - prev_alt
        if dz <= 0:
            continue
            
        # Lift parcel to current level
        alt_diff_km = (current_alt - surface['altitude']) / 1000
        
        if not lcl_found and parcel_temp - alt_diff_km * dry_lapse <= parcel_dewpoint:
            # Reached LCL
            lcl_found = True
            lcl_alt = surface['altitude'] + (parcel_temp - parcel_dewpoint) / dry_lapse * 1000
            parcel_temp_at_level = parcel_dewpoint
        elif not lcl_found:
            # Below LCL - dry adiabatic
            parcel_temp_at_level = parcel_temp - alt_diff_km * dry_lapse
        else:
            # Above LCL - moist adiabatic
            lcl_alt_diff_km = (current_alt - lcl_alt) / 1000 if 'lcl_alt' in locals() else alt_diff_km
            parcel_temp_at_level = parcel_dewpoint - lcl_alt_diff_km * moist_lapse
        
        # Calculate buoyancy
        temp_diff = parcel_temp_at_level - env_temp
        env_temp_k = env_temp + 273.15
        buoyancy = g * temp_diff / env_temp_k * dz
        
        if temp_diff > 0:
            if not lfc_found:
                lfc_found = True
            cape += buoyancy
        elif not lfc_found:
            cin += abs(buoyancy)
    
    return cape, cin

def detect_inversions(df):
    """Detect temperature inversions."""
    inversions = []
    in_inversion = False
    inversion_start = None
    inversion_start_temp = None
    
    for i in range(1, len(df)):
        current_temp = df.iloc[i]['temperature']
        prev_temp = df.iloc[i-1]['temperature']
        current_alt = df.iloc[i]['altitude']
        prev_alt = df.iloc[i-1]['altitude']
        
        if current_temp > prev_temp and not in_inversion:
            # Start of inversion
            in_inversion = True
            inversion_start = prev_alt
            inversion_start_temp = prev_temp
        elif current_temp <= prev_temp and in_inversion:
            # End of inversion
            in_inversion = False
            strength = current_temp - inversion_start_temp
            inversions.append({
                'base_altitude_m': inversion_start,
                'top_altitude_m': prev_alt,
                'strength_C': strength
            })
    
    # Handle case where inversion continues to top of sounding
    if in_inversion:
        strength = df.iloc[-1]['temperature'] - inversion_start_temp
        inversions.append({
            'base_altitude_m': inversion_start,
            'top_altitude_m': df.iloc[-1]['altitude'],
            'strength_C': strength
        })
    
    return inversions

def main():
    parser = argparse.ArgumentParser(description='Analyze radiosonde atmospheric sounding data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} not found")
        return
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Load data
        df = pd.read_csv(args.input)
        
        # Validate required columns
        required_cols = ['pressure', 'temperature', 'dewpoint', 'wind_speed', 'wind_direction', 'altitude']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            print(f"Error: Missing required columns: {missing_cols}")
            return
        
        # Clean and sort data
        df = df.dropna(subset=['pressure', 'temperature', 'altitude']).copy()
        df = df.sort_values('altitude').reset_index(drop=True)
        
        if len(df) < 10:
            print("Error: Insufficient data points (minimum 10 required)")
            return
        
        # Calculate lapse rates
        df['lapse_rate'] = calculate_lapse_rates(df)
        
        # Find tropopause
        tropopause_height, tropopause_pressure = find_tropopause(df)
        
        # Calculate CAPE and CIN
        cape, cin = calculate_cape_cin(df)
        
        # Detect inversions
        inversions = detect_inversions(df)
        
        # Prepare summary
        summary = {
            'tropopause_height_m': tropopause_height,
            'tropopause_pressure_hPa': tropopause_pressure,
            'CAPE_J_kg': round(cape, 1),
            'CIN_J_kg': round(cin, 1),
            'inversions': inversions,
            'surface_temperature_C': df.iloc[0]['temperature'],
            'surface_dewpoint_C': df.iloc[0]['dewpoint']
        }
        
        # Save outputs
        df.to_csv(output_dir / 'processed_profile.csv', index=False)
        
        with open(output_dir / 'summary.json', 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Print summary
        print(f"Tropopause height: {tropopause_height} m" if tropopause_height else "Tropopause: Not found")
        print(f"CAPE: {cape:.1f} J/kg")
        print(f"CIN: {cin:.1f} J/kg")
        print(f"Number of inversions: {len(inversions)}")
        
        print(f"\nOutputs saved to {output_dir}")
        
    except Exception as e:
        print(f"Error processing data: {e}")

if __name__ == "__main__":
    main()
