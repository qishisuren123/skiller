#!/usr/bin/env python3
"""
Atmospheric Ozone Profile Analysis Tool
Processes ozonesonde balloon measurements for atmospheric research
"""

import argparse
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.integrate import trapz

def quality_control_ozone(ozone, max_ozone=20.0):
    """Apply quality control filters to ozone data"""
    mask = (ozone >= 0) & (ozone <= max_ozone) & np.isfinite(ozone)
    return mask

def calculate_lapse_rate(altitude, temperature):
    """Calculate temperature lapse rate in K/km"""
    return -np.gradient(temperature, altitude)

def find_tropopause(altitude, temperature, min_alt=6.0, layer_depth=2.0):
    """Find tropopause using WMO thermal definition"""
    lapse_rates = calculate_lapse_rate(altitude, temperature)
    
    for i, alt in enumerate(altitude):
        if alt < min_alt:
            continue
            
        # Find indices for 2 km layer above current point
        layer_mask = (altitude >= alt) & (altitude <= alt + layer_depth)
        if np.sum(layer_mask) < 3:  # Need minimum points for averaging
            continue
            
        avg_lapse = np.mean(lapse_rates[layer_mask])
        if avg_lapse < 2.0:  # Less than 2 K/km
            return alt
    
    return None

def integrate_ozone_column(altitude, pressure, ozone, alt_min=0, alt_max=np.inf):
    """Integrate ozone column between altitude limits (returns Dobson Units)"""
    mask = (altitude >= alt_min) & (altitude <= alt_max) & np.isfinite(ozone)
    if np.sum(mask) < 2:
        return 0.0
    
    alt_subset = altitude[mask]
    p_subset = pressure[mask]
    o3_subset = ozone[mask]
    
    # Convert mPa to mixing ratio and integrate
    # Simplified conversion: 1 DU ≈ 2.69e16 molecules/cm²
    # Ozone partial pressure to column conversion
    dp = -np.gradient(p_subset)  # Pressure difference (positive)
    column = np.sum(o3_subset * dp / 9.81)  # Simplified integration
    
    return column * 0.01  # Convert to Dobson Units (approximate)

def find_ozone_maximum(altitude, ozone, min_alt=10.0):
    """Find altitude and concentration of ozone maximum above min_alt"""
    mask = altitude >= min_alt
    if np.sum(mask) == 0:
        return None, None
    
    subset_alt = altitude[mask]
    subset_o3 = ozone[mask]
    
    max_idx = np.argmax(subset_o3)
    return subset_alt[max_idx], subset_o3[max_idx]

def exponential_decay(alt, a, b, h):
    """Exponential decay model for ozone scale height"""
    return a * np.exp(-(alt - b) / h)

def calculate_scale_height(altitude, ozone, alt_min, alt_max):
    """Calculate ozone scale height by exponential fitting"""
    mask = (altitude >= alt_min) & (altitude <= alt_max) & np.isfinite(ozone)
    if np.sum(mask) < 5:
        return None
    
    alt_subset = altitude[mask]
    o3_subset = ozone[mask]
    
    try:
        # Initial parameter guess
        p0 = [np.max(o3_subset), np.min(alt_subset), 7.0]
        popt, _ = curve_fit(exponential_decay, alt_subset, o3_subset, p0=p0)
        return abs(popt[2])  # Scale height
    except:
        return None

def create_profile_plot(altitude, ozone, tropopause_alt, ozone_max_alt, output_path):
    """Create publication-quality ozone profile plot"""
    fig, ax = plt.subplots(figsize=(8, 10))
    
    ax.plot(ozone, altitude, 'b-', linewidth=2, label='Ozone Profile')
    
    if tropopause_alt:
        ax.axhline(y=tropopause_alt, color='red', linestyle='--', 
                  linewidth=2, label=f'Tropopause ({tropopause_alt:.1f} km)')
    
    if ozone_max_alt:
        ax.axhline(y=ozone_max_alt, color='green', linestyle=':', 
                  linewidth=2, label=f'O₃ Maximum ({ozone_max_alt:.1f} km)')
    
    ax.set_xlabel('Ozone Concentration (mPa)', fontsize=12)
    ax.set_ylabel('Altitude (km)', fontsize=12)
    ax.set_title('Ozonesonde Profile Analysis', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_ylim(0, min(35, np.max(altitude)))
    ax.set_xlim(0, np.max(ozone) * 1.1)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze ozonesonde vertical profiles')
    parser.add_argument('input_file', help='Input CSV file with ozonesonde data')
    parser.add_argument('--output-json', default='ozone_analysis.json', 
                       help='Output JSON summary file')
    parser.add_argument('--output-plot', default='ozone_profile.png', 
                       help='Output plot file')
    parser.add_argument('--max-ozone', type=float, default=20.0,
                       help='Maximum realistic ozone concentration (mPa)')
    parser.add_argument('--min-tropopause', type=float, default=6.0,
                       help='Minimum tropopause altitude (km)')
    
    args = parser.parse_args()
    
    # Load data
    try:
        data = pd.read_csv(args.input_file)
        altitude = data['altitude_km'].values
        pressure = data['pressure_hPa'].values  
        temperature = data['temperature_K'].values
        ozone = data['ozone_mPa'].values
    except Exception as e:
        print(f"Error loading data: {e}")
        return 1
    
    # Quality control
    qc_mask = quality_control_ozone(ozone, args.max_ozone)
    altitude = altitude[qc_mask]
    pressure = pressure[qc_mask]
    temperature = temperature[qc_mask]
    ozone = ozone[qc_mask]
    
    print(f"Data points after QC: {len(altitude)}")
    
    # Find tropopause
    tropopause_alt = find_tropopause(altitude, temperature, args.min_tropopause)
    print(f"Tropopause altitude: {tropopause_alt:.1f} km" if tropopause_alt else "Tropopause not found")
    
    # Calculate columns
    if tropopause_alt:
        trop_column = integrate_ozone_column(altitude, pressure, ozone, 0, tropopause_alt)
        strat_column = integrate_ozone_column(altitude, pressure, ozone, tropopause_alt, 30)
    else:
        trop_column = strat_column = 0.0
    
    # Find ozone maximum
    ozone_max_alt, ozone_max_conc = find_ozone_maximum(altitude, ozone, 
                                                      tropopause_alt or 10.0)
    
    # Calculate scale height
    if tropopause_alt:
        scale_height = calculate_scale_height(altitude, ozone, 
                                            tropopause_alt + 5, tropopause_alt + 15)
    else:
        scale_height = None
    
    # Prepare results
    results = {
        'tropopause_height_km': tropopause_alt,
        'tropospheric_column_DU': round(trop_column, 2) if trop_column else None,
        'stratospheric_column_DU': round(strat_column, 2) if strat_column else None,
        'ozone_maximum_altitude_km': round(ozone_max_alt, 1) if ozone_max_alt else None,
        'ozone_maximum_concentration_mPa': round(ozone_max_conc, 2) if ozone_max_conc else None,
        'stratospheric_scale_height_km': round(scale_height, 1) if scale_height else None,
        'data_points_processed': len(altitude)
    }
    
    # Save JSON summary
    with open(args.output_json, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create plot
    create_profile_plot(altitude, ozone, tropopause_alt, ozone_max_alt, args.output_plot)
    
    print(f"Analysis complete. Results saved to {args.output_json}")
    print(f"Profile plot saved to {args.output_plot}")
    
    return 0

if __name__ == '__main__':
    exit(main())
