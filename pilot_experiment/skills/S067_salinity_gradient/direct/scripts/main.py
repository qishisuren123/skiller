#!/usr/bin/env python3
"""
Estuarine Salinity Gradient Analysis from CTD Transects
Analyzes salinity gradients, stratification, and mixing in estuarine environments
"""

import argparse
import json
import numpy as np
import pandas as pd
import h5py
from scipy.interpolate import griddata
from scipy.integrate import trapz
import os
from typing import Dict, List, Tuple, Optional

def seawater_density(temperature, salinity, pressure=0):
    """Calculate seawater density using UNESCO equation of state"""
    # Simplified UNESCO formula for surface pressure
    T = temperature
    S = salinity
    
    # Pure water density
    rho_w = (999.842594 + 6.793952e-2*T - 9.095290e-3*T**2 + 
             1.001685e-4*T**3 - 1.120083e-6*T**4 + 6.536332e-9*T**5)
    
    # Salinity contribution
    A = (8.24493e-1 - 4.0899e-3*T + 7.6438e-5*T**2 - 8.2467e-7*T**3 + 5.3875e-9*T**4)
    B = (-5.72466e-3 + 1.0227e-4*T - 1.6546e-6*T**2)
    C = 4.8314e-4
    
    rho = rho_w + A*S + B*S**(3/2) + C*S**2
    return rho

def detect_halocline(depth, salinity, min_gradient=0.5, min_thickness=2.0):
    """Detect halocline layers in CTD profile"""
    if len(depth) < 3:
        return []
    
    # Smooth data and calculate gradient
    sal_smooth = np.convolve(salinity, np.ones(3)/3, mode='same')
    dsal_dz = np.gradient(sal_smooth, depth)
    
    # Find regions exceeding gradient threshold
    strong_gradient = np.abs(dsal_dz) > min_gradient
    
    # Identify continuous regions meeting thickness criteria
    regions = []
    in_region = False
    start_idx = 0
    
    for i, is_strong in enumerate(strong_gradient):
        if is_strong and not in_region:
            start_idx = i
            in_region = True
        elif not is_strong and in_region:
            thickness = depth[i-1] - depth[start_idx]
            if thickness >= min_thickness:
                max_grad_idx = start_idx + np.argmax(np.abs(dsal_dz[start_idx:i]))
                regions.append({
                    'depth_range': [float(depth[start_idx]), float(depth[i-1])],
                    'max_gradient': float(dsal_dz[max_grad_idx]),
                    'thickness': float(thickness)
                })
            in_region = False
    
    # Handle case where region extends to end
    if in_region:
        thickness = depth[-1] - depth[start_idx]
        if thickness >= min_thickness:
            max_grad_idx = start_idx + np.argmax(np.abs(dsal_dz[start_idx:]))
            regions.append({
                'depth_range': [float(depth[start_idx]), float(depth[-1])],
                'max_gradient': float(dsal_dz[max_grad_idx]),
                'thickness': float(thickness)
            })
    
    return regions

def calculate_simpson_parameter(depth, temperature, salinity):
    """Calculate Simpson's Stratification Parameter"""
    if len(depth) < 2:
        return 0.0
    
    g = 9.81  # m/s²
    rho_0 = 1025.0  # kg/m³
    
    # Calculate density profile
    density = seawater_density(temperature, salinity)
    rho_surface = density[0]
    
    # Calculate stratification parameter
    integrand = (density - rho_surface) * depth
    phi = (g / rho_0) * trapz(integrand, depth)
    
    return float(phi)

def classify_stratification(phi):
    """Classify stratification based on Simpson's parameter"""
    if phi < 10:
        return "well-mixed"
    elif phi < 50:
        return "partially-mixed"
    else:
        return "stratified"

def find_salt_wedge(depth, salinity, target_salinity=2.0):
    """Find salt wedge intrusion (2 PSU isohaline)"""
    if len(depth) < 2:
        return None
    
    # Find where salinity crosses target value
    for i in range(len(salinity) - 1):
        if ((salinity[i] <= target_salinity <= salinity[i+1]) or 
            (salinity[i+1] <= target_salinity <= salinity[i])):
            # Linear interpolation to find exact crossing depth
            frac = (target_salinity - salinity[i]) / (salinity[i+1] - salinity[i])
            crossing_depth = depth[i] + frac * (depth[i+1] - depth[i])
            return float(crossing_depth)
    
    return None

def calculate_richardson_number(depth, temperature, salinity):
    """Calculate Richardson number for mixing analysis"""
    if len(depth) < 3:
        return np.array([])
    
    g = 9.81
    density = seawater_density(temperature, salinity)
    
    # Calculate buoyancy frequency squared (N²)
    drho_dz = np.gradient(density, depth)
    N_squared = -(g / np.mean(density)) * drho_dz
    
    # Simplified shear calculation (assuming horizontal velocity ~ 0.1 m/s over 1m)
    # In practice, this would come from ADCP or current meter data
    S_squared = np.full_like(N_squared, 0.01)  # Typical estuarine shear
    
    # Richardson number
    Ri = N_squared / (S_squared + 1e-10)  # Avoid division by zero
    
    return Ri

def calculate_mixing_efficiency(Ri):
    """Calculate mixing efficiency parameter"""
    eta = Ri / (Ri + 0.2)
    return eta

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points on Earth"""
    R = 6371000  # Earth radius in meters
    
    dlat = np.radians(lat2 - lat1)
    dlon = np.radians(lon2 - lon1)
    
    a = (np.sin(dlat/2)**2 + 
         np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlon/2)**2)
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
    
    return R * c

def quality_control(depth, temperature, salinity):
    """Apply quality control checks to CTD data"""
    flags = []
    
    # Check for salinity jumps
    if len(salinity) > 1:
        sal_diff = np.abs(np.diff(salinity))
        jump_indices = np.where(sal_diff > 2.0)[0]
        for idx in jump_indices:
            flags.append({
                'type': 'salinity_jump',
                'depth': float(depth[idx]),
                'value': float(sal_diff[idx]),
                'description': f'Salinity jump of {sal_diff[idx]:.2f} PSU'
            })
    
    # Check for density inversions
    if len(depth) > 1:
        density = seawater_density(temperature, salinity)
        density_diff = np.diff(density)
        inversion_indices = np.where(density_diff < -0.1)[0]
        for idx in inversion_indices:
            flags.append({
                'type': 'density_inversion',
                'depth': float(depth[idx]),
                'value': float(density_diff[idx]),
                'description': f'Density inversion of {density_diff[idx]:.3f} kg/m³'
            })
    
    return flags

def optimal_interpolation_2d(stations_data, grid_x, grid_y, decorr_x=500, decorr_y=5):
    """Perform optimal interpolation of salinity field"""
    # Extract observation points and values
    obs_points = []
    obs_values = []
    
    for station in stations_data:
        lat, lon = station['latitude'], station['longitude']
        for i, depth in enumerate(station['depth']):
            obs_points.append([lon, depth])  # x, y coordinates
            obs_values.append(station['salinity'][i])
    
    if len(obs_points) < 3:
        # Not enough data for interpolation
        return np.full((len(grid_y), len(grid_x)), np.nan)
    
    obs_points = np.array(obs_points)
    obs_values = np.array(obs_values)
    
    # Create grid points
    grid_points = np.array([[x, y] for y in grid_y for x in grid_x])
    
    # Simple griddata interpolation (linear)
    grid_values = griddata(obs_points, obs_values, grid_points, method='linear')
    
    # Reshape to 2D grid
    interpolated_field = grid_values.reshape(len(grid_y), len(grid_x))
    
    return interpolated_field

def main():
    parser = argparse.ArgumentParser(description='Estuarine Salinity Gradient Analysis')
    parser.add_argument('--input', required=True, help='Input JSON file with CTD data')
    parser.add_argument('--output-dir', required=True, help='Output directory')
    parser.add_argument('--transect-id', required=True, help='Transect identifier')
    parser.add_argument('--river-mouth-lat', type=float, required=True, help='River mouth latitude')
    parser.add_argument('--river-mouth-lon', type=float, required=True, help='River mouth longitude')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load input data
    with open(args.input, 'r') as f:
        data = json.load(f)
    
    stations = data['stations']
    
    # Initialize results
    haloclines_results = []
    stratification_results = []
    salt_wedge_results = []
    mixing_results = []
    quality_results = []
    
    # Process each station
    for station in stations:
        station_id = station['station_id']
        lat, lon = station['latitude'], station['longitude']
        depth = np.array(station['depth'])
        temperature = np.array(station['temperature'])
        salinity = np.array(station['salinity'])
        
        # Quality control
        qc_flags = quality_control(depth, temperature, salinity)
        if qc_flags:
            quality_results.append({
                'station_id': station_id,
                'latitude': lat,
                'longitude': lon,
                'flags': qc_flags
            })
        
        # Halocline detection
        haloclines = detect_halocline(depth, salinity)
        if haloclines:
            haloclines_results.append({
                'station_id': station_id,
                'latitude': lat,
                'longitude': lon,
                'haloclines': haloclines
            })
        
        # Stratification analysis
        phi = calculate_simpson_parameter(depth, temperature, salinity)
        stratification_results.append({
            'station_id': station_id,
            'latitude': lat,
            'longitude': lon,
            'simpson_parameter': phi,
            'classification': classify_stratification(phi)
        })
        
        # Salt wedge analysis
        salt_wedge_depth = find_salt_wedge(depth, salinity)
        if salt_wedge_depth is not None:
            distance_from_mouth = haversine_distance(
                args.river_mouth_lat, args.river_mouth_lon, lat, lon
            )
            salt_wedge_results.append({
                'station_id': station_id,
                'latitude': lat,
                'longitude': lon,
                'intrusion_depth': salt_wedge_depth,
                'distance_from_mouth': distance_from_mouth
            })
        
        # Mixing efficiency analysis
        Ri = calculate_richardson_number(depth, temperature, salinity)
        if len(Ri) > 0:
            eta = calculate_mixing_efficiency(Ri)
            active_mixing_depths = depth[1:-1][eta < 0.15]  # Adjust indexing for gradient
            
            mixing_results.append({
                'station_id': station_id,
                'latitude': lat,
                'longitude': lon,
                'richardson_numbers': Ri.tolist(),
                'mixing_efficiency': eta.tolist(),
                'active_mixing_depths': active_mixing_depths.tolist()
            })
    
    # Generate interpolated field
    # Create regular grid
    lats = [s['latitude'] for s in stations]
    lons = [s['longitude'] for s in stations]
    depths = []
    for s in stations:
        depths.extend(s['depth'])
    
    if lats and lons and depths:
        grid_x = np.arange(min(lons), max(lons), 0.001)  # ~50m spacing
        grid_y = np.arange(0, max(depths), 0.5)  # 0.5m depth spacing
        
        interpolated_field = optimal_interpolation_2d(stations, grid_x, grid_y)
        
        # Save interpolated field to HDF5
        with h5py.File(os.path.join(args.output_dir, 'interpolated_field.h5'), 'w') as f:
            f.create_dataset('salinity', data=interpolated_field)
            f.create_dataset('longitude', data=grid_x)
            f.create_dataset('depth', data=grid_y)
            f.attrs['transect_id'] = args.transect_id
    
    # Save results
    with open(os.path.join(args.output_dir, 'haloclines.json'), 'w') as f:
        json.dump(haloclines_results, f, indent=2)
    
    with open(os.path.join(args.output_dir, 'stratification.json'), 'w') as f:
        json.dump(stratification_results, f, indent=2)
    
    with open(os.path.join(args.output_dir, 'salt_wedge.json'), 'w') as f:
        json.dump(salt_wedge_results, f, indent=2)
    
    with open(os.path.join(args.output_dir, 'mixing_zones.json'), 'w') as f:
        json.dump(mixing_results, f, indent=2)
    
    with open(os.path.join(args.output_dir, 'quality_flags.json'), 'w') as f:
        json.dump(quality_results, f, indent=2)
    
    print(f"Analysis complete. Results saved to {args.output_dir}")
    print(f"Processed {len(stations)} stations")
    print(f"Found {len(haloclines_results)} stations with haloclines")
    print(f"Detected salt wedge at {len(salt_wedge_results)} stations")
    print(f"Quality flags raised for {len(quality_results)} stations")

if __name__ == '__main__':
    main()
