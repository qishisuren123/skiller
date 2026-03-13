#!/usr/bin/env python3
"""
XRD Pattern Analysis Tool
Analyzes X-ray diffraction patterns with background subtraction, peak detection, 
Gaussian fitting, and d-spacing calculations.
"""

import argparse
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import warnings
warnings.filterwarnings('ignore')

def gaussian(x, amplitude, center, sigma):
    """Gaussian function for peak fitting."""
    return amplitude * np.exp(-(x - center)**2 / (2 * sigma**2))

def subtract_background(intensity, window_size=50, smooth_window=10):
    """
    Subtract background using rolling minimum approach.
    
    Args:
        intensity: pandas Series of intensity values
        window_size: window for rolling minimum (background estimation)
        smooth_window: window for smoothing the background
    
    Returns:
        tuple: (background, corrected_intensity)
    """
    # Estimate background with rolling minimum
    background = intensity.rolling(window=window_size, center=True, min_periods=1).min()
    
    # Smooth the background
    background_smooth = background.rolling(window=smooth_window, center=True, min_periods=1).mean()
    
    # Subtract background
    corrected = intensity - background_smooth
    corrected = np.maximum(corrected, 0)  # Ensure non-negative values
    
    return background_smooth, corrected

def fit_gaussian_peak(two_theta, intensity, peak_idx, window_half_width=20):
    """
    Fit Gaussian to a single peak.
    
    Args:
        two_theta: array of two_theta values
        intensity: array of intensity values
        peak_idx: index of peak center
        window_half_width: half-width of fitting window in data points
    
    Returns:
        dict: fitted parameters or None if fitting fails
    """
    # Define fitting window
    start_idx = max(0, peak_idx - window_half_width)
    end_idx = min(len(two_theta), peak_idx + window_half_width + 1)
    
    x_fit = two_theta[start_idx:end_idx]
    y_fit = intensity[start_idx:end_idx]
    
    if len(x_fit) < 5:  # Need minimum points for fitting
        return None
    
    # Initial parameter estimates
    amplitude_init = intensity[peak_idx]
    center_init = two_theta[peak_idx]
    sigma_init = 0.1  # Initial guess for peak width
    
    try:
        # Fit Gaussian with bounds
        popt, pcov = curve_fit(
            gaussian, x_fit, y_fit,
            p0=[amplitude_init, center_init, sigma_init],
            bounds=([0, center_init-1, 0.01], [amplitude_init*2, center_init+1, 2.0]),
            maxfev=1000
        )
        
        amplitude, center, sigma = popt
        fwhm = 2.3548 * sigma  # Convert sigma to FWHM
        
        return {
            'amplitude': amplitude,
            'center': center,
            'sigma': sigma,
            'fwhm': fwhm
        }
    
    except Exception as e:
        print(f"Warning: Gaussian fitting failed for peak at {two_theta[peak_idx]:.2f}°: {e}")
        return None

def calculate_d_spacing(two_theta_deg, wavelength):
    """Calculate d-spacing using Bragg's law."""
    theta_rad = np.radians(two_theta_deg / 2)
    d_spacing = wavelength / (2 * np.sin(theta_rad))
    return d_spacing

def analyze_xrd_pattern(input_file, output_dir, wavelength, min_height, prominence):
    """Main analysis function."""
    
    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Load data
    print(f"Loading XRD data from {input_file}")
    try:
        data = pd.read_csv(input_file)
        if 'two_theta' not in data.columns or 'intensity' not in data.columns:
            raise ValueError("CSV must contain 'two_theta' and 'intensity' columns")
    except Exception as e:
        raise ValueError(f"Error loading input file: {e}")
    
    # Validate data
    if len(data) < 50:
        raise ValueError("Insufficient data points for analysis")
    
    two_theta = data['two_theta'].values
    raw_intensity = data['intensity'].values
    
    print(f"Loaded {len(data)} data points")
    print(f"Two-theta range: {two_theta.min():.2f}° to {two_theta.max():.2f}°")
    
    # Background subtraction
    print("Performing background subtraction...")
    background, corrected_intensity = subtract_background(data['intensity'])
    
    # Peak detection
    print(f"Detecting peaks (min_height={min_height}, prominence={prominence})...")
    peaks, properties = find_peaks(corrected_intensity, height=min_height, prominence=prominence)
    
    print(f"Found {len(peaks)} peaks")
    
    if len(peaks) == 0:
        print("No peaks found. Consider adjusting --min-height or --prominence parameters.")
        return
    
    # Fit Gaussians and calculate d-spacings
    print("Fitting Gaussian peaks and calculating d-spacings...")
    peak_results = []
    fitted_intensity = np.zeros_like(corrected_intensity)
    
    for i, peak_idx in enumerate(peaks):
        peak_two_theta = two_theta[peak_idx]
        peak_intensity = corrected_intensity[peak_idx]
        
        # Fit Gaussian
        fit_result = fit_gaussian_peak(two_theta, corrected_intensity, peak_idx)
        
        if fit_result is not None:
            # Calculate d-spacing
            d_spacing = calculate_d_spacing(fit_result['center'], wavelength)
            
            # Add fitted Gaussian to total fit
            gaussian_curve = gaussian(two_theta, fit_result['amplitude'], 
                                    fit_result['center'], fit_result['sigma'])
            fitted_intensity += gaussian_curve
            
            peak_results.append({
                'peak_id': i + 1,
                'two_theta': fit_result['center'],
                'intensity': fit_result['amplitude'],
                'fwhm': fit_result['fwhm'],
                'd_spacing': d_spacing
            })
        else:
            # Use detected peak position if fitting failed
            d_spacing = calculate_d_spacing(peak_two_theta, wavelength)
            peak_results.append({
                'peak_id': i + 1,
                'two_theta': peak_two_theta,
                'intensity': peak_intensity,
                'fwhm': np.nan,
                'd_spacing': d_spacing
            })
    
    # Find strongest peak
    strongest_peak = max(peak_results, key=lambda x: x['intensity'])
    
    # Save results
    print("Saving results...")
    
    # 1. Save peaks.csv
    peaks_df = pd.DataFrame(peak_results)
    peaks_df.to_csv(os.path.join(output_dir, 'peaks.csv'), index=False)
    
    # 2. Save fitted_pattern.csv
    pattern_df = pd.DataFrame({
        'two_theta': two_theta,
        'raw_intensity': raw_intensity,
        'background': background,
        'corrected_intensity': corrected_intensity,
        'fitted_intensity': fitted_intensity
    })
    pattern_df.to_csv(os.path.join(output_dir, 'fitted_pattern.csv'), index=False)
    
    # 3. Save summary.json
    summary = {
        'n_peaks': len(peak_results),
        'wavelength': wavelength,
        'strongest_peak': {
            'two_theta': strongest_peak['two_theta'],
            'd_spacing': strongest_peak['d_spacing'],
            'intensity': strongest_peak['intensity']
        },
        'peaks': peak_results
    }
    
    with open(os.path.join(output_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Print summary
    print(f"\nAnalysis complete!")
    print(f"Number of peaks found: {len(peak_results)}")
    print(f"Strongest peak: {strongest_peak['two_theta']:.3f}° (d = {strongest_peak['d_spacing']:.3f} Å)")
    print(f"Results saved to: {output_dir}")

def main():
    parser = argparse.ArgumentParser(description='Analyze X-ray diffraction patterns')
    parser.add_argument('--input', required=True, help='Input CSV file with two_theta and intensity columns')
    parser.add_argument('--output', required=True, help='Output directory for results')
    parser.add_argument('--wavelength', type=float, default=1.5406, 
                       help='X-ray wavelength in Angstroms (default: 1.5406 for Cu K-alpha)')
    parser.add_argument('--min-height', type=float, default=50, 
                       help='Minimum peak height in counts (default: 50)')
    parser.add_argument('--prominence', type=float, default=30, 
                       help='Minimum peak prominence (default: 30)')
    
    args = parser.parse_args()
    
    try:
        analyze_xrd_pattern(args.input, args.output, args.wavelength, 
                          args.min_height, args.prominence)
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())
