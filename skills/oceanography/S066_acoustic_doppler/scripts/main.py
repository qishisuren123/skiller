#!/usr/bin/env python3
"""
ADCP Velocity Profile Quality Control and Analysis
Processes acoustic Doppler current profiler data with sophisticated QC algorithms
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
import json
import logging
from scipy import signal
from scipy.stats import median_abs_deviation
import sys

def load_adcp_data(filename):
    """
    Load ADCP data from CSV files with proper NaN handling
    """
    try:
        # Read CSV with pandas, handling various NaN representations
        df = pd.read_csv(filename, na_values=['NaN', 'nan', 'NAN', '', 'null', 'NULL'])
        
        # Convert to numpy array, assuming single column of data
        if df.shape[1] == 1:
            data = df.iloc[:, 0].values
        else:
            # If multiple columns, take all as 2D array
            data = df.values
            
        return data
        
    except Exception as e:
        logging.error(f"Error loading {filename}: {e}")
        raise

def phase_space_spike_detection(u, v, w, dt=1.0, threshold=2.0):
    """
    Detect velocity spikes using phase-space method with proper NaN handling
    """
    # Initialize spike mask with False values
    spikes = np.zeros(len(u), dtype=bool)
    
    for vel_component in [u, v, w]:
        if len(vel_component) < 3:
            continue
        
        # Skip if all values are NaN
        if np.all(np.isnan(vel_component)):
            continue
            
        # Calculate first derivative, preserving NaN locations
        dvel_dt = np.gradient(vel_component, dt)
        
        # Create masks for valid (non-NaN) data
        valid_vel = ~np.isnan(vel_component)
        valid_dvel = ~np.isnan(dvel_dt)
        valid_both = valid_vel & valid_dvel
        
        if np.sum(valid_both) < 2:
            continue
        
        # Calculate phase space radius only for valid points
        radius = np.full_like(vel_component, np.nan)
        radius[valid_both] = np.sqrt(vel_component[valid_both]**2 + dvel_dt[valid_both]**2)
        
        # Calculate statistics only from valid radius values
        valid_radius = radius[~np.isnan(radius)]
        if len(valid_radius) < 2:
            continue
            
        mean_radius = np.mean(valid_radius)
        std_radius = np.std(valid_radius)
        
        # Create spike mask, ensuring we only flag valid data points
        threshold_value = mean_radius + threshold * std_radius
        component_spikes = np.zeros_like(radius, dtype=bool)
        
        # Only compare valid radius values
        valid_radius_mask = ~np.isnan(radius)
        component_spikes[valid_radius_mask] = radius[valid_radius_mask] > threshold_value
        
        # Combine with overall spike mask
        spikes = spikes | component_spikes
    
    return spikes

def correlation_filter(u, v, w, correlations, threshold=70.0):
    """
    Filter velocities based on beam correlation values
    """
    # Handle both 1D and 2D correlation arrays
    if correlations.ndim == 1:
        bad_correlation = correlations < threshold
        # Handle NaN correlations
        bad_correlation = bad_correlation | np.isnan(correlations)
    else:
        # If 2D, take minimum across beams
        min_correlation = np.nanmin(correlations, axis=1)
        bad_correlation = (min_correlation < threshold) | np.isnan(min_correlation)
    
    u_filtered = u.copy()
    v_filtered = v.copy() 
    w_filtered = w.copy()
    
    u_filtered[bad_correlation] = np.nan
    v_filtered[bad_correlation] = np.nan
    w_filtered[bad_correlation] = np.nan
    
    return u_filtered, v_filtered, w_filtered, bad_correlation

def echo_intensity_analysis(echo_intensity, window_size=5, noise_threshold=10.0):
    """
    Identify weak acoustic returns using sliding window
    """
    # Handle NaN values in echo intensity
    if np.all(np.isnan(echo_intensity)):
        return np.ones_like(echo_intensity, dtype=bool)
    
    # Apply sliding window median filter, handling NaN
    echo_clean = echo_intensity.copy()
    nan_mask = np.isnan(echo_clean)
    
    if np.any(~nan_mask):
        # Interpolate NaN values for filtering
        valid_indices = np.where(~nan_mask)[0]
        if len(valid_indices) > 1:
            echo_clean[nan_mask] = np.interp(
                np.where(nan_mask)[0], 
                valid_indices, 
                echo_intensity[valid_indices]
            )
    
    filtered_echo = signal.medfilt(echo_clean, kernel_size=window_size)
    
    # Flag regions below noise threshold or originally NaN
    weak_signal = (filtered_echo < noise_threshold) | nan_mask
    
    return weak_signal

def vertical_shear_validation(u, v, depths, shear_limit=0.1):
    """
    Calculate and validate vertical shear with NaN handling
    """
    # Skip if insufficient data
    if len(u) < 3 or np.sum(~np.isnan(u)) < 3:
        return np.full_like(u, np.nan), np.full_like(v, np.nan), np.zeros_like(u, dtype=bool)
    
    dz = np.gradient(depths)
    
    # Handle NaN values in gradient calculation
    du_dz = np.gradient(u) / dz
    dv_dz = np.gradient(v) / dz
    
    # Apply median filter to smooth shear estimates, handling NaN
    du_dz_clean = du_dz.copy()
    dv_dz_clean = dv_dz.copy()
    
    # Only apply median filter to non-NaN values
    du_nan_mask = np.isnan(du_dz)
    dv_nan_mask = np.isnan(dv_dz)
    
    if not np.all(du_nan_mask):
        du_dz_clean[~du_nan_mask] = signal.medfilt(du_dz[~du_nan_mask], kernel_size=min(3, np.sum(~du_nan_mask)))
    
    if not np.all(dv_nan_mask):
        dv_dz_clean[~dv_nan_mask] = signal.medfilt(dv_dz[~dv_nan_mask], kernel_size=min(3, np.sum(~dv_nan_mask)))
    
    # Flag unrealistic shear, treating NaN as not excessive
    excessive_shear = np.zeros_like(u, dtype=bool)
    valid_du = ~np.isnan(du_dz_clean)
    valid_dv = ~np.isnan(dv_dz_clean)
    
    excessive_shear[valid_du] = excessive_shear[valid_du] | (np.abs(du_dz_clean[valid_du]) > shear_limit)
    excessive_shear[valid_dv] = excessive_shear[valid_dv] | (np.abs(dv_dz_clean[valid_dv]) > shear_limit)
    
    return du_dz_clean, dv_dz_clean, excessive_shear

def safe_json_convert(value):
    """
    Convert numpy values to JSON-safe format, handling NaN
    """
    if isinstance(value, (np.integer, np.floating)):
        if np.isnan(value) or np.isinf(value):
            return None
        return float(value)
    return value

def compute_statistics(u_qc, v_qc, w_qc, depths):
    """
    Compute oceanographic statistics from QC'd data
    """
    # Remove NaN values for statistics - use QC'd data
    valid_u = u_qc[~np.isnan(u_qc)]
    valid_v = v_qc[~np.isnan(v_qc)]
    valid_w = w_qc[~np.isnan(w_qc)]
    
    # Calculate statistics
    depth_avg_u = np.mean(valid_u) if len(valid_u) > 0 else np.nan
    depth_avg_v = np.mean(valid_v) if len(valid_v) > 0 else np.nan
    depth_avg_w = np.mean(valid_w) if len(valid_w) > 0 else np.nan
    max_speed = np.max(np.sqrt(valid_u**2 + valid_v**2)) if len(valid_u) > 0 and len(valid_v) > 0 else np.nan
    data_quality = (len(valid_u) / len(u_qc)) * 100
    u_std = np.std(valid_u) if len(valid_u) > 0 else np.nan
    v_std = np.std(valid_v) if len(valid_v) > 0 else np.nan
    
    # Convert to JSON-safe format
    stats = {
        'depth_averaged_u': safe_json_convert(depth_avg_u),
        'depth_averaged_v': safe_json_convert(depth_avg_v),
        'depth_averaged_w': safe_json_convert(depth_avg_w),
        'max_speed': safe_json_convert(max_speed),
        'data_quality_percent': safe_json_convert(data_quality),
        'u_std': safe_json_convert(u_std),
        'v_std': safe_json_convert(v_std)
    }
    
    return stats

def plot_profiles(u_orig, v_orig, u_qc, v_qc, depths, correlations, bad_data, output_file):
    """
    Generate comprehensive velocity profile plots
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 8))
    
    # Velocity profiles
    axes[0].plot(u_orig, depths, 'r-', alpha=0.5, label='Original U')
    axes[0].plot(v_orig, depths, 'b-', alpha=0.5, label='Original V')
    axes[0].plot(u_qc, depths, 'r-', linewidth=2, label='QC U')
    axes[0].plot(v_qc, depths, 'b-', linewidth=2, label='QC V')
    axes[0].set_xlabel('Velocity (m/s)')
    axes[0].set_ylabel('Depth (m)')
    axes[0].legend()
    axes[0].grid(True)
    axes[0].set_title('Velocity Profiles')
    axes[0].invert_yaxis()
    
    # Correlation values
    if correlations.ndim == 1:
        axes[1].plot(correlations, depths, 'g-')
    else:
        axes[1].plot(np.nanmean(correlations, axis=1), depths, 'g-')
    axes[1].set_xlabel('Correlation (%)')
    axes[1].set_ylabel('Depth (m)')
    axes[1].grid(True)
    axes[1].set_title('Beam Correlation')
    axes[1].invert_yaxis()
    
    # Data quality flags
    axes[2].scatter(bad_data.astype(int), depths, c=bad_data, cmap='RdYlGn_r', alpha=0.6)
    axes[2].set_xlabel('Bad Data Flag')
    axes[2].set_ylabel('Depth (m)')
    axes[2].set_title('Quality Control Flags')
    axes[2].invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    parser = argparse.ArgumentParser(description='ADCP Quality Control and Analysis')
    parser.add_argument('--u_data', required=True, help='U velocity component CSV file')
    parser.add_argument('--v_data', required=True, help='V velocity component CSV file') 
    parser.add_argument('--w_data', required=True, help='W velocity component CSV file')
    parser.add_argument('--correlations', required=True, help='Beam correlation CSV file')
    parser.add_argument('--echo_intensity', required=True, help='Echo intensity CSV file')
    parser.add_argument('--depths', required=True, help='Depth bins CSV file')
    parser.add_argument('--output', default='adcp_qc_results.json', help='Output JSON file')
    parser.add_argument('--plot', default='adcp_profiles.png', help='Output plot file')
    parser.add_argument('--correlation_threshold', type=float, default=70.0, help='Correlation threshold (%)')
    parser.add_argument('--spike_threshold', type=float, default=2.0, help='Spike detection threshold (std devs)')
    
    args = parser.parse_args()
    
    try:
        # Load data using improved CSV loader
        logging.info("Loading ADCP data files...")
        u = load_adcp_data(args.u_data)
        v = load_adcp_data(args.v_data)
        w = load_adcp_data(args.w_data)
        correlations = load_adcp_data(args.correlations)
        echo_intensity = load_adcp_data(args.echo_intensity)
        depths = load_adcp_data(args.depths)
        
        logging.info(f"Data loaded: {len(u)} depth bins")
        
        # Apply QC procedures
        logging.info("Applying quality control procedures...")
        spikes = phase_space_spike_detection(u, v, w, threshold=args.spike_threshold)
        u_corr, v_corr, w_corr, bad_corr = correlation_filter(u, v, w, correlations, args.correlation_threshold)
        weak_signal = echo_intensity_analysis(echo_intensity)
        du_dz, dv_dz, excessive_shear = vertical_shear_validation(u_corr, v_corr, depths)
        
        # Combine all QC flags
        bad_data = spikes | bad_corr | weak_signal | excessive_shear
        
        # Apply final QC
        u_qc = u.copy()
        v_qc = v.copy()
        w_qc = w.copy()
        
        u_qc[bad_data] = np.nan
        v_qc[bad_data] = np.nan
        w_qc[bad_data] = np.nan
        
        # Compute statistics on QC'd data
        stats = compute_statistics(u_qc, v_qc, w_qc, depths)
        
        # Generate plots
        plot_profiles(u, v, u_qc, v_qc, depths, correlations, bad_data, args.plot)
        
        # Save results
        with open(args.output, 'w') as f:
            json.dump(stats, f, indent=2)
        
        logging.info(f"Quality control complete. Results saved to {args.output}")
        logging.info(f"Data quality: {stats['data_quality_percent']:.1f}%")
        
    except Exception as e:
        logging.error(f"Error processing ADCP data: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
