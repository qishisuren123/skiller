import numpy as np
import matplotlib.pyplot as plt
import argparse
import json
import logging
from pathlib import Path
import os
import time as time_module

def generate_spirometry_data(n_points=1000, sampling_rate=100):
    """Generate synthetic spirometry flow-volume data"""
    # Time array based on sampling rate
    duration = n_points / sampling_rate  # seconds
    time = np.linspace(0, duration, n_points)
    
    # Create a realistic flow pattern: inspiration followed by forced expiration
    flow = np.zeros(n_points)
    
    # Inspiration phase (first 20% of time) - positive flow
    insp_end = int(0.2 * n_points)
    insp_time = np.linspace(0, np.pi, insp_end)
    flow[:insp_end] = 6 * np.sin(insp_time)
    
    # Brief pause at peak inspiration
    pause_end = int(0.25 * n_points)
    flow[insp_end:pause_end] = 0
    
    # Forced expiration phase (remaining 75%) - negative flow
    exp_points = n_points - pause_end
    exp_time = np.arange(exp_points) / sampling_rate
    # Exponential decay for realistic expiratory flow (negative values)
    peak_exp_flow = -8.0
    flow[pause_end:] = peak_exp_flow * np.exp(-1.2 * exp_time) * (1 + 0.15 * np.sin(12 * exp_time))
    
    # Calculate volume by integrating flow (vectorized operation)
    dt = 1.0 / sampling_rate
    volume = np.cumsum(flow) * dt
    
    # Normalize volume to start at residual volume and reach realistic TLC
    volume = volume - np.min(volume) + 1.5  # Start at 1.5L (RV)
    max_vol = np.max(volume)
    if max_vol > 1.5:
        volume = 1.5 + (volume - 1.5) * (6.5 / (max_vol - 1.5))  # Scale to realistic TLC
    
    return time, flow, volume

def calculate_fev1_optimized(time, flow, volume, sampling_rate=100):
    """Optimized FEV1 calculation for large datasets"""
    # Find start of forced expiration (maximum negative flow)
    exp_start_idx = np.argmin(flow)
    
    # Calculate one second later using sampling rate (much faster than time search)
    one_sec_points = int(sampling_rate * 1.0)
    one_sec_idx = min(exp_start_idx + one_sec_points, len(volume) - 1)
    
    # FEV1 is volume exhaled (decrease in volume) in first second
    fev1 = volume[exp_start_idx] - volume[one_sec_idx]
    
    return max(0, fev1)

def calculate_fvc_optimized(time, flow, volume):
    """Optimized FVC calculation for large datasets"""
    # Find start of forced expiration (maximum negative flow)
    exp_start_idx = np.argmin(flow)
    start_volume = volume[exp_start_idx]
    
    # Use vectorized operations to find end of expiration
    # Look in the latter portion of the data for efficiency
    search_start = exp_start_idx + int(0.1 * len(flow))
    search_region = flow[search_start:]
    
    # Find where flow approaches zero using vectorized comparison
    end_candidates = np.where(search_region > -0.3)[0]
    
    if len(end_candidates) > 0:
        exp_end_idx = search_start + end_candidates[0]
    else:
        exp_end_idx = len(flow) - 1
    
    # FVC is total volume exhaled during forced expiration
    end_volume = volume[exp_end_idx]
    fvc = start_volume - end_volume
    
    return max(0, fvc)

def validate_spirometry_parameters(fev1, fvc, fev1_fvc_ratio):
    """Validate that spirometry parameters are within physiological ranges"""
    warnings = []
    errors = []
    
    # FEV1 validation (typical range: 2.5-5.0L for healthy adults)
    if fev1 < 1.0:
        errors.append(f"FEV1 ({fev1:.3f}L) is critically low (< 1.0L)")
    elif fev1 < 2.0:
        warnings.append(f"FEV1 ({fev1:.3f}L) is below normal range (< 2.0L)")
    elif fev1 > 6.0:
        warnings.append(f"FEV1 ({fev1:.3f}L) is unusually high (> 6.0L)")
    
    # FVC validation (typical range: 3.0-6.0L for healthy adults)
    if fvc < 1.5:
        errors.append(f"FVC ({fvc:.3f}L) is critically low (< 1.5L)")
    elif fvc < 2.5:
        warnings.append(f"FVC ({fvc:.3f}L) is below normal range (< 2.5L)")
    elif fvc > 7.0:
        warnings.append(f"FVC ({fvc:.3f}L) is unusually high (> 7.0L)")
    
    # FEV1/FVC ratio validation (normal: > 0.70, obstruction if < 0.70)
    if fev1_fvc_ratio < 0.50:
        errors.append(f"FEV1/FVC ratio ({fev1_fvc_ratio:.3f}) indicates severe obstruction (< 0.50)")
    elif fev1_fvc_ratio < 0.70:
        warnings.append(f"FEV1/FVC ratio ({fev1_fvc_ratio:.3f}) suggests airway obstruction (< 0.70)")
    elif fev1_fvc_ratio > 1.0:
        errors.append(f"FEV1/FVC ratio ({fev1_fvc_ratio:.3f}) is impossible (> 1.0)")
    
    # FEV1 should not exceed FVC
    if fev1 > fvc:
        errors.append(f"FEV1 ({fev1:.3f}L) cannot exceed FVC ({fvc:.3f}L)")
    
    return warnings, errors

def create_flow_volume_plot(flow, volume, output_file, downsample_factor=10):
    """Create and save flow-volume loop plot with optional downsampling for large datasets"""
    
    # Downsample for plotting if dataset is large (improves performance and file size)
    if len(flow) > 5000:
        indices = np.arange(0, len(flow), downsample_factor)
        plot_flow = flow[indices]
        plot_volume = volume[indices]
        logging.info(f"Downsampling plot data by factor of {downsample_factor} for performance")
    else:
        plot_flow = flow
        plot_volume = volume
    
    plt.figure(figsize=(10, 8))
    plt.plot(plot_volume, plot_flow, 'b-', linewidth=2)
    plt.xlabel('Volume (L)')
    plt.ylabel('Flow Rate (L/s)')
    plt.title('Flow-Volume Loop')
    plt.grid(True, alpha=0.3)
    plt.axhline(y=0, color='k', linestyle='--', alpha=0.5)
    
    # Add annotations for inspiration and expiration
    max_vol_idx = np.argmax(plot_volume)
    plt.annotate('Peak Inspiration', xy=(plot_volume[max_vol_idx], plot_flow[max_vol_idx]), 
                xytext=(plot_volume[max_vol_idx]-1, 2), fontsize=10,
                arrowprops=dict(arrowstyle='->', color='green'))
    
    min_flow_idx = np.argmin(plot_flow)
    plt.annotate('Peak Expiration', xy=(plot_volume[min_flow_idx], plot_flow[min_flow_idx]), 
                xytext=(plot_volume[min_flow_idx]+1, plot_flow[min_flow_idx]-1), fontsize=10,
                arrowprops=dict(arrowstyle='->', color='red'))
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Spirometry Flow-Volume Analysis')
    parser.add_argument('--n-points', type=int, default=1000, 
                       help='Number of data points to generate')
    parser.add_argument('--plot-file', type=str, default='flow_volume_loop.png',
                       help='Output plot filename')
    parser.add_argument('--results-file', type=str, default='spirometry_results.json',
                       help='Output JSON results filename')
    
    args = parser.parse_args()
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Ensure output directories exist BEFORE generating data
    plot_path = Path(args.plot_file)
    plot_path.parent.mkdir(parents=True, exist_ok=True)
    
    results_path = Path(args.results_file)
    results_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating {args.n_points} data points")
    
    # Generate synthetic data
    time, flow, volume = generate_spirometry_data(args.n_points)
    
    # Calculate spirometry parameters using optimized functions
    fev1 = calculate_fev1_optimized(time, flow, volume)
    fvc = calculate_fvc_optimized(time, flow, volume)
    fev1_fvc_ratio = fev1 / fvc if fvc > 0 else 0
    
    # Validate parameters
    warnings, errors = validate_spirometry_parameters(fev1, fvc, fev1_fvc_ratio)
    
    # Log validation results
    for warning in warnings:
        logger.warning(warning)
    for error in errors:
        logger.error(error)
    
    # Create results dictionary
    results = {
        'FEV1_L': round(fev1, 3),
        'FVC_L': round(fvc, 3),
        'FEV1_FVC_ratio': round(fev1_fvc_ratio, 3),
        'data_points': args.n_points,
        'sampling_rate_Hz': 100,
        'validation': {
            'warnings': warnings,
            'errors': errors
        }
    }
    
    # Save results to JSON
    with open(args.results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Create and save plot
    create_flow_volume_plot(flow, volume, args.plot_file)
    
    logger.info(f"Results: FEV1={fev1:.3f}L, FVC={fvc:.3f}L, Ratio={fev1_fvc_ratio:.3f}")
    logger.info(f"Plot saved to {args.plot_file}")
    logger.info(f"Results saved to {args.results_file}")
    
    # Debug info
    logger.info(f"Volume range: {np.min(volume):.2f}L to {np.max(volume):.2f}L")
    logger.info(f"Flow range: {np.min(flow):.2f}L/s to {np.max(flow):.2f}L/s")

if __name__ == "__main__":
    main()
