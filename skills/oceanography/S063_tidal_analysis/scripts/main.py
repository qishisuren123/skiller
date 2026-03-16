import numpy as np
import matplotlib.pyplot as plt
import json
import csv
import argparse
import logging
from scipy import signal
from datetime import datetime, timedelta
import sys

# Known tidal constituents (name, period in hours)
TIDAL_CONSTITUENTS = {
    'M2': 12.42,
    'S2': 12.00,
    'O1': 25.82,
    'K1': 23.93,
    'N2': 12.66
}

def estimate_memory_usage(duration_days, sampling_interval_hours):
    """Estimate memory usage for the analysis"""
    total_hours = duration_days * 24
    n_points = int(total_hours / sampling_interval_hours)
    
    # Memory for time array, tidal heights, FFT result (complex), and working arrays
    # Each float64 is 8 bytes, complex128 is 16 bytes
    time_memory = n_points * 8  # time array
    data_memory = n_points * 8  # tidal heights
    fft_memory = n_points * 16  # complex FFT result
    working_memory = n_points * 8 * 4  # various working arrays
    
    total_memory = time_memory + data_memory + fft_memory + working_memory
    return n_points, total_memory

def generate_synthetic_tidal_data(duration_days, sampling_interval_hours, random_seed=None):
    """Generate synthetic tidal height data with known constituents"""
    
    if random_seed is not None:
        np.random.seed(random_seed)
        logging.info(f"Using random seed: {random_seed}")
    
    # Estimate and check memory usage
    n_points, memory_bytes = estimate_memory_usage(duration_days, sampling_interval_hours)
    memory_mb = memory_bytes / (1024 * 1024)
    memory_gb = memory_mb / 1024
    
    logging.info(f"Estimated data points: {n_points:,}")
    logging.info(f"Estimated memory usage: {memory_mb:.1f} MB ({memory_gb:.2f} GB)")
    
    # Set reasonable limits
    MAX_POINTS = 500000  # ~500k points max
    MAX_MEMORY_GB = 2.0  # 2GB max
    
    if n_points > MAX_POINTS:
        raise ValueError(f"Too many data points ({n_points:,}). Maximum allowed: {MAX_POINTS:,}")
    
    if memory_gb > MAX_MEMORY_GB:
        raise ValueError(f"Estimated memory usage ({memory_gb:.2f} GB) exceeds limit ({MAX_MEMORY_GB} GB)")
    
    # Time array
    total_hours = duration_days * 24
    time_hours = np.arange(0, total_hours, sampling_interval_hours)
    
    # Initialize tidal heights
    tidal_heights = np.zeros(len(time_hours))
    
    # Add major constituents with realistic amplitudes
    constituents_used = {
        'M2': {'amplitude': 1.5, 'phase': np.random.uniform(0, 2*np.pi)},
        'S2': {'amplitude': 0.8, 'phase': np.random.uniform(0, 2*np.pi)},
        'O1': {'amplitude': 0.6, 'phase': np.random.uniform(0, 2*np.pi)}
    }
    
    for name, params in constituents_used.items():
        period = TIDAL_CONSTITUENTS[name]
        omega = 2 * np.pi / period
        tidal_heights += params['amplitude'] * np.cos(omega * time_hours + params['phase'])
    
    # Add Gaussian noise
    noise = np.random.normal(0, 0.1, len(time_hours))
    tidal_heights += noise
    
    return time_hours, tidal_heights, constituents_used

def perform_harmonic_analysis(time_hours, tidal_heights, min_amplitude):
    """Perform FFT-based harmonic analysis"""
    
    # Calculate frequency resolution
    total_duration_hours = time_hours[-1] - time_hours[0]
    freq_resolution = 1.0 / total_duration_hours  # cycles per hour
    period_resolution = 1.0 / freq_resolution     # hours
    
    logging.info(f"Frequency resolution: {freq_resolution:.6f} cycles/hour")
    logging.info(f"Period resolution: {period_resolution:.2f} hours")
    
    # Remove mean (detrend)
    tidal_heights_detrended = tidal_heights - np.mean(tidal_heights)
    
    # Compute FFT
    logging.info("Computing FFT...")
    fft_result = np.fft.fft(tidal_heights_detrended)
    frequencies = np.fft.fftfreq(len(tidal_heights_detrended), time_hours[1] - time_hours[0])
    
    # Only positive frequencies
    positive_freq_idx = frequencies > 0
    frequencies = frequencies[positive_freq_idx]
    fft_result = fft_result[positive_freq_idx]
    
    # Convert to periods (hours)
    periods = 1.0 / frequencies
    
    # Calculate amplitudes and phases correctly
    amplitudes = np.abs(fft_result) * 2.0 / len(tidal_heights_detrended)
    
    # Phase calculation: convert from complex angle, adjust for cosine convention
    phases = -np.angle(fft_result) * 180.0 / np.pi
    # Normalize phases to [0, 360)
    phases = (phases + 360) % 360
    
    # Find constituents with adaptive tolerance based on frequency resolution
    identified_constituents = []
    
    # Calculate adaptive tolerance - should be at least 2x the frequency resolution
    base_tolerance = 0.05  # 5% base tolerance
    resolution_tolerance = 2.0 * period_resolution / 12.0  # Scale by typical tidal period
    adaptive_tolerance = max(base_tolerance, resolution_tolerance)
    
    logging.info(f"Using tolerance: {adaptive_tolerance:.3f}")
    
    for i, (period, amplitude, phase) in enumerate(zip(periods, amplitudes, phases)):
        if amplitude >= min_amplitude and period > 1.0:  # Skip very short periods
            # Match to known constituents with adaptive tolerance
            best_match = None
            best_error = float('inf')
            
            for const_name, const_period in TIDAL_CONSTITUENTS.items():
                relative_error = abs(period - const_period) / const_period
                if relative_error < adaptive_tolerance and relative_error < best_error:
                    best_match = const_name
                    best_error = relative_error
            
            if best_match:
                identified_constituents.append({
                    'constituent': best_match,
                    'period_hours': float(period),
                    'amplitude_m': float(amplitude),
                    'phase_degrees': float(phase),
                    'frequency_error': float(best_error)
                })
    
    # Sort by amplitude (descending)
    identified_constituents.sort(key=lambda x: x['amplitude_m'], reverse=True)
    
    # Remove duplicate constituents (keep the one with higher amplitude)
    unique_constituents = []
    used_names = set()
    for const in identified_constituents:
        if const['constituent'] not in used_names:
            unique_constituents.append(const)
            used_names.add(const['constituent'])
            # Remove frequency_error from final output
            del const['frequency_error']
    
    return unique_constituents

def save_results_csv(constituents, output_path):
    """Save results to CSV format"""
    if not constituents:
        logging.warning("No constituents to save to CSV")
        return
    
    with open(output_path, 'w', newline='') as csvfile:
        fieldnames = ['constituent', 'period_hours', 'amplitude_m', 'phase_degrees']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for const in constituents:
            writer.writerow(const)
    
    logging.info(f"Saved CSV results to {output_path}")

def create_plot(time_hours, tidal_heights, output_path):
    """Create time series plot"""
    # For very large datasets, subsample for plotting
    if len(time_hours) > 10000:
        step = len(time_hours) // 10000
        time_plot = time_hours[::step]
        heights_plot = tidal_heights[::step]
        logging.info(f"Subsampling plot data: using every {step}th point")
    else:
        time_plot = time_hours
        heights_plot = tidal_heights
    
    plt.figure(figsize=(12, 6))
    plt.plot(time_plot, heights_plot, 'b-', linewidth=0.8)
    plt.xlabel('Time (hours)')
    plt.ylabel('Tidal Height (m)')
    plt.title('Synthetic Tidal Height Time Series')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Tidal Harmonic Analysis Tool')
    parser.add_argument('--duration', type=int, required=True, 
                       help='Duration in days')
    parser.add_argument('--sampling_interval', type=float, required=True, 
                       help='Sampling interval in hours')
    parser.add_argument('--output_harmonics', type=str, required=True, 
                       help='Path to save JSON results')
    parser.add_argument('--output_plot', type=str, required=True, 
                       help='Path to save PNG plot')
    parser.add_argument('--min_amplitude', type=float, required=True, 
                       help='Minimum amplitude threshold (m)')
    parser.add_argument('--output_csv', type=str, 
                       help='Optional path to save CSV results')
    parser.add_argument('--random_seed', type=int, 
                       help='Random seed for reproducible results')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.duration <= 0:
        raise ValueError("Duration must be positive")
    if args.sampling_interval <= 0:
        raise ValueError("Sampling interval must be positive")
    if args.min_amplitude < 0:
        raise ValueError("Minimum amplitude must be non-negative")
    
    # Validate sampling interval isn't too fine
    if args.sampling_interval < 0.05:  # 3 minutes
        raise ValueError("Sampling interval too fine (< 0.05 hours). Use >= 0.05 hours (3 minutes)")
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Warn about frequency resolution issues
    if args.duration < 3:
        logging.warning(f"Short duration ({args.duration} days) may result in poor frequency resolution")
        logging.warning("Consider using duration >= 3 days for better constituent separation")
    
    logging.info(f"Generating synthetic tidal data for {args.duration} days")
    time_hours, tidal_heights, true_constituents = generate_synthetic_tidal_data(
        args.duration, args.sampling_interval, args.random_seed)
    
    logging.info("Performing harmonic analysis")
    identified_constituents = perform_harmonic_analysis(
        time_hours, tidal_heights, args.min_amplitude)
    
    # Save JSON results
    with open(args.output_harmonics, 'w') as f:
        json.dump(identified_constituents, f, indent=2)
    
    logging.info(f"Saved {len(identified_constituents)} constituents to {args.output_harmonics}")
    
    # Save CSV results if requested
    if args.output_csv:
        save_results_csv(identified_constituents, args.output_csv)
    
    # Create plot
    create_plot(time_hours, tidal_heights, args.output_plot)
    logging.info(f"Saved plot to {args.output_plot}")
    
    # Log true vs identified for comparison
    logging.info("True constituents used in generation:")
    for name, params in true_constituents.items():
        logging.info(f"  {name}: amplitude={params['amplitude']:.2f}m, phase={params['phase']*180/np.pi:.1f}°")

if __name__ == "__main__":
    main()
