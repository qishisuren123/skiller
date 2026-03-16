#!/usr/bin/env python3
"""
Solar Flare Detection and Classification Tool
Analyzes X-ray light curve data to detect and classify solar flare events.
"""

import argparse
import json
import logging
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import random

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def generate_synthetic_data(duration_hours=24, resolution_minutes=1):
    """Generate synthetic X-ray light curve data with embedded flares"""
    logging.info(f"Generating {duration_hours}h of synthetic data with {resolution_minutes}min resolution")
    
    # Create time array
    total_minutes = duration_hours * 60
    n_points = int(total_minutes / resolution_minutes)
    times = np.arange(n_points) * resolution_minutes
    
    logging.debug(f"Created {n_points} data points")
    
    # Baseline flux with noise
    baseline_flux = 1e-6  # W/m^2
    noise_level = baseline_flux * 0.1
    flux = np.random.normal(baseline_flux, noise_level, n_points)
    
    # Add flares
    n_flares = random.randint(3, 8)
    flare_info = []
    
    for i in range(n_flares):
        # Random flare parameters
        start_idx = random.randint(int(100/resolution_minutes), 
                                 n_points - int(200/resolution_minutes))
        duration_minutes = random.randint(10, 60)  # 10-60 minutes
        duration_points = int(duration_minutes / resolution_minutes)  # Convert to points
        peak_multiplier = random.choice([2, 5, 15, 50, 150])  # Different classes
        
        # Gaussian flare profile
        flare_indices = np.arange(duration_points)
        if duration_points > 0:
            flare_profile = np.exp(-0.5 * ((flare_indices - duration_points/2) / (duration_points/4 + 0.1))**2)
        else:
            flare_profile = np.array([1.0])  # Single point flare
            duration_points = 1
        
        peak_flux = baseline_flux * peak_multiplier
        
        # Add flare to data
        end_idx = min(start_idx + duration_points, n_points)
        actual_duration_points = end_idx - start_idx
        actual_duration_minutes = actual_duration_points * resolution_minutes
        
        if actual_duration_points > 0:
            flux[start_idx:end_idx] += peak_flux * flare_profile[:actual_duration_points]
            
            flare_info.append({
                'start_time': times[start_idx],
                'peak_time': times[start_idx + actual_duration_points//2],
                'end_time': times[end_idx-1],
                'peak_flux': peak_flux + baseline_flux,
                'duration': actual_duration_minutes
            })
            
            logging.debug(f"Added flare {i+1}: start_idx={start_idx}, duration_points={actual_duration_points}, "
                         f"duration_minutes={actual_duration_minutes}")
    
    return times, flux, baseline_flux, flare_info

def detect_flares(times, flux, baseline_flux, threshold_sigma=3, min_duration_minutes=5, resolution_minutes=1):
    """Detect flare events using threshold-based algorithm with robust noise estimation"""
    logging.info("Detecting flare events...")
    
    # Robust threshold calculation with multiple fallback methods
    try:
        # Method 1: Use quiet periods (flux < 2x baseline)
        quiet_flux = flux[flux < baseline_flux * 2]
        if len(quiet_flux) > 10:  # Need sufficient quiet data
            noise_std = np.std(quiet_flux)
            logging.debug(f"Using quiet period noise estimation: {len(quiet_flux)} points")
        else:
            raise ValueError("Insufficient quiet periods")
    except (ValueError, IndexError):
        try:
            # Method 2: Use lower percentile of all data
            noise_std = np.std(flux[flux < np.percentile(flux, 30)])
            logging.debug("Using 30th percentile noise estimation")
        except:
            # Method 3: Fallback to known noise level
            noise_std = baseline_flux * 0.1
            logging.debug("Using fallback noise estimation")
    
    threshold = baseline_flux + threshold_sigma * noise_std
    logging.debug(f"Detection threshold: {threshold:.2e} W/m², noise_std: {noise_std:.2e}")
    
    # Find points above threshold
    above_threshold = flux > threshold
    
    # Find continuous regions
    detected_flares = []
    in_flare = False
    start_idx = 0
    min_duration_points = max(1, int(min_duration_minutes / resolution_minutes))
    
    logging.debug(f"Minimum duration: {min_duration_minutes} min = {min_duration_points} points")
    
    for i, is_above in enumerate(above_threshold):
        if is_above and not in_flare:
            start_idx = i
            in_flare = True
        elif not is_above and in_flare:
            duration_points = (i - start_idx)
            duration_minutes = duration_points * resolution_minutes
            if duration_points >= min_duration_points:  # Check duration in points
                peak_idx = start_idx + np.argmax(flux[start_idx:i])
                detected_flares.append({
                    'start_time': float(times[start_idx]),
                    'peak_time': float(times[peak_idx]),
                    'end_time': float(times[i-1]),
                    'peak_flux': float(flux[peak_idx]),
                    'duration': float(duration_minutes)
                })
                logging.debug(f"Detected flare: start={times[start_idx]:.1f}, duration={duration_minutes:.1f} min")
            in_flare = False
    
    # Handle case where flare extends to end of data
    if in_flare:
        duration_points = len(flux) - start_idx
        duration_minutes = duration_points * resolution_minutes
        if duration_points >= min_duration_points:
            peak_idx = start_idx + np.argmax(flux[start_idx:])
            detected_flares.append({
                'start_time': float(times[start_idx]),
                'peak_time': float(times[peak_idx]),
                'end_time': float(times[-1]),
                'peak_flux': float(flux[peak_idx]),
                'duration': float(duration_minutes)
            })
            logging.debug(f"Detected flare at end: start={times[start_idx]:.1f}, duration={duration_minutes:.1f} min")
    
    return detected_flares

def classify_flares(flares, baseline_flux):
    """Classify flares into C/M/X categories"""
    for flare in flares:
        ratio = flare['peak_flux'] / baseline_flux
        if ratio >= 100:
            flare['classification'] = 'X'
        elif ratio >= 10:
            flare['classification'] = 'M'
        else:
            flare['classification'] = 'C'
        logging.debug(f"Flare ratio: {ratio:.1f}x baseline -> Class {flare['classification']}")
    
    return flares

def save_results(flares, output_file):
    """Save detection results to JSON file"""
    logging.info(f"Saving results to {output_file}")
    with open(output_file, 'w') as f:
        json.dump(flares, f, indent=2)

def plot_results(times, flux, flares, output_plot):
    """Generate visualization of light curve with detected flares"""
    logging.info(f"Generating plot: {output_plot}")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Plot light curve
    ax.plot(times/60, flux, 'b-', alpha=0.7, label='X-ray flux')
    
    # Highlight detected flares
    colors = {'C': 'green', 'M': 'orange', 'X': 'red'}
    labels_added = set()  # Track which labels we've already added
    
    for flare in flares:
        start_hour = flare['start_time'] / 60
        end_hour = flare['end_time'] / 60
        peak_hour = flare['peak_time'] / 60
        classification = flare['classification']
        
        # Only add label if we haven't seen this classification before
        label = f"Class {classification}" if classification not in labels_added else None
        if label:
            labels_added.add(classification)
        
        ax.axvspan(start_hour, end_hour, alpha=0.3, 
                  color=colors[classification], label=label)
        ax.plot(peak_hour, flare['peak_flux'], 'o', 
               color=colors[classification], markersize=8)
    
    ax.set_xlabel('Time (hours)')
    ax.set_ylabel('X-ray Flux (W/m²)')
    ax.set_title('Solar Flare Detection Results')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(output_plot, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Solar Flare Detection and Classification')
    parser.add_argument('--duration', type=int, default=24, 
                       help='Duration in hours (default: 24)')
    parser.add_argument('--resolution', type=int, default=1,
                       help='Time resolution in minutes (default: 1)')
    parser.add_argument('--output-json', default='flare_results.json',
                       help='Output JSON file (default: flare_results.json)')
    parser.add_argument('--output-plot', default='flare_lightcurve.png',
                       help='Output plot file (default: flare_lightcurve.png)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Generate synthetic data
    times, flux, baseline_flux, true_flares = generate_synthetic_data(
        args.duration, args.resolution)
    
    # Detect flares
    detected_flares = detect_flares(times, flux, baseline_flux, 
                                   resolution_minutes=args.resolution)
    
    # Classify flares
    classified_flares = classify_flares(detected_flares, baseline_flux)
    
    # Save results
    save_results(classified_flares, args.output_json)
    
    # Generate plot
    plot_results(times, flux, classified_flares, args.output_plot)
    
    logging.info(f"Analysis complete. Detected {len(classified_flares)} flares.")
    for flare in classified_flares:
        logging.info(f"Class {flare['classification']} flare: "
                    f"Peak at {flare['peak_time']:.1f} min, "
                    f"Duration: {flare['duration']:.1f} min")

if __name__ == '__main__':
    main()
