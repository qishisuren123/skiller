import argparse
import pandas as pd
import numpy as np
import json
from pathlib import Path
from scipy.signal import find_peaks
from scipy.ndimage import minimum_filter1d, gaussian_filter1d
from scipy.optimize import curve_fit
import warnings

def gaussian(x, A, mu, sigma):
    """Gaussian function for peak fitting"""
    return A * np.exp(-(x - mu)**2 / (2 * sigma**2))

def subtract_background(two_theta, intensity, window_size=50):
    """Estimate and subtract background using rolling minimum with edge case handling"""
    # Handle case where window is larger than data
    actual_window = min(window_size, len(intensity) // 3)
    actual_window = max(actual_window, 3)  # Minimum window size
    
    # Use minimum filter to estimate background
    background = minimum_filter1d(intensity, size=actual_window, mode='nearest')
    # Smooth the background
    background = gaussian_filter1d(background, sigma=max(2, actual_window//10))
    
    # Subtract background
    corrected_intensity = intensity - background
    # Ensure no negative values
    corrected_intensity = np.maximum(corrected_intensity, 0)
    
    return background, corrected_intensity

def detect_peaks(two_theta, corrected_intensity, min_height, prominence):
    """Detect peaks with validation for low signal data"""
    # Check if data has sufficient signal
    max_intensity = np.max(corrected_intensity)
    mean_intensity = np.mean(corrected_intensity)
    noise_level = np.std(corrected_intensity)
    
    print(f"Signal analysis: max={max_intensity:.1f}, mean={mean_intensity:.1f}, noise={noise_level:.1f}")
    
    # Adaptive thresholds for low signal data
    if max_intensity < min_height:
        print(f"Warning: Maximum intensity ({max_intensity:.1f}) below min_height ({min_height})")
        print("Reducing thresholds for low signal data...")
        min_height = max_intensity * 0.3  # 30% of max signal
        prominence = max(prominence * 0.5, noise_level * 2)  # Reduce prominence but stay above noise
    
    # Additional check for very noisy data
    if noise_level > mean_intensity:
        print("Warning: High noise level detected. Results may be unreliable.")
        prominence = max(prominence, noise_level * 3)  # Increase prominence for noisy data
    
    peaks, properties = find_peaks(corrected_intensity, 
                                 height=min_height, 
                                 prominence=prominence)
    
    return peaks, properties

def fit_gaussian_peaks(two_theta, corrected_intensity, peaks):
    """Fit Gaussian curves to detected peaks with proper baseline handling"""
    fitted_peaks = []
    
    for i, peak_idx in enumerate(peaks):
        # Define fitting window around peak (adaptive window size)
        peak_pos = two_theta[peak_idx]
        peak_height = corrected_intensity[peak_idx]
        
        # Estimate peak width by finding half-maximum points
        half_max = peak_height / 2
        left_idx = peak_idx
        right_idx = peak_idx
        
        # Find left half-maximum
        while left_idx > 0 and corrected_intensity[left_idx] > half_max:
            left_idx -= 1
        
        # Find right half-maximum
        while right_idx < len(corrected_intensity) - 1 and corrected_intensity[right_idx] > half_max:
            right_idx += 1
        
        # Estimated FWHM and sigma
        estimated_fwhm = two_theta[right_idx] - two_theta[left_idx]
        estimated_sigma = estimated_fwhm / 2.3548
        
        # Define fitting window (3 sigma on each side, minimum 1 degree)
        window_size = max(3 * estimated_sigma, 1.0)
        window_mask = (two_theta >= peak_pos - window_size) & (two_theta <= peak_pos + window_size)
        
        x_fit = two_theta[window_mask]
        y_fit = corrected_intensity[window_mask]  # Use corrected intensity directly
        
        if len(x_fit) < 5:  # Need minimum points for fitting
            continue
            
        # Better initial parameter estimates
        A_init = peak_height
        mu_init = peak_pos
        sigma_init = max(estimated_sigma, 0.1)  # Ensure reasonable minimum
        
        try:
            # Fit Gaussian directly to background-corrected data
            popt, pcov = curve_fit(gaussian, x_fit, y_fit, 
                                 p0=[A_init, mu_init, sigma_init],
                                 bounds=([0, peak_pos-window_size/2, 0.05], 
                                        [A_init*3, peak_pos+window_size/2, window_size]),
                                 maxfev=2000)
            
            A, mu, sigma = popt
            fwhm = 2.3548 * sigma  # Convert sigma to FWHM
            
            # Quality check: fitted peak should be reasonable
            if 0.05 < sigma < 5.0 and abs(mu - peak_pos) < window_size/2:
                fitted_peaks.append({
                    'peak_id': i + 1,
                    'two_theta': mu,
                    'intensity': A,  # Keep as background-corrected intensity
                    'fwhm': fwhm,
                    'sigma': sigma
                })
            else:
                print(f"Warning: Peak at {peak_pos:.2f}° failed quality check")
                
        except Exception as e:
            print(f"Warning: Failed to fit peak at {peak_pos:.2f}°: {e}")
            # Fallback: use detected peak position with estimated parameters
            fitted_peaks.append({
                'peak_id': i + 1,
                'two_theta': peak_pos,
                'intensity': peak_height,
                'fwhm': estimated_fwhm,
                'sigma': estimated_sigma
            })
            continue
    
    return fitted_peaks

def calculate_d_spacings(fitted_peaks, wavelength):
    """Calculate d-spacings using Bragg's law"""
    for peak in fitted_peaks:
        theta_rad = np.radians(peak['two_theta'] / 2)  # Convert to radians and divide by 2
        d_spacing = wavelength / (2 * np.sin(theta_rad))
        peak['d_spacing'] = d_spacing
    
    return fitted_peaks

def generate_fitted_pattern(two_theta, fitted_peaks, background):
    """Generate fitted intensity pattern from all fitted Gaussians plus background"""
    fitted_intensity = background.copy()  # Start with background
    
    for peak in fitted_peaks:
        peak_contribution = gaussian(two_theta, peak['intensity'], 
                                   peak['two_theta'], peak['sigma'])
        fitted_intensity += peak_contribution  # Add peak contributions
    
    return fitted_intensity

def save_outputs(output_dir, two_theta, intensity, background, corrected_intensity, 
                fitted_intensity, fitted_peaks, wavelength):
    """Save all output files with handling for no peaks case"""
    
    # Save peaks.csv (handle empty case)
    if fitted_peaks:
        peaks_df = pd.DataFrame(fitted_peaks)
        peaks_df = peaks_df[['peak_id', 'two_theta', 'intensity', 'fwhm', 'd_spacing']]
    else:
        # Create empty DataFrame with correct columns
        peaks_df = pd.DataFrame(columns=['peak_id', 'two_theta', 'intensity', 'fwhm', 'd_spacing'])
    
    peaks_df.to_csv(output_dir / 'peaks.csv', index=False)
    
    # Save fitted_pattern.csv
    pattern_df = pd.DataFrame({
        'two_theta': two_theta,
        'raw_intensity': intensity,
        'background': background,
        'corrected_intensity': corrected_intensity,
        'fitted_intensity': fitted_intensity
    })
    pattern_df.to_csv(output_dir / 'fitted_pattern.csv', index=False)
    
    # Save summary.json (handle no peaks case)
    summary = {
        'n_peaks': len(fitted_peaks),
        'wavelength': wavelength,
        'data_quality': {
            'max_intensity': float(np.max(intensity)),
            'mean_intensity': float(np.mean(intensity)),
            'noise_level': float(np.std(corrected_intensity)),
            'signal_to_noise': float(np.max(corrected_intensity) / np.std(corrected_intensity)) if np.std(corrected_intensity) > 0 else 0
        },
        'peaks': []
    }
    
    if fitted_peaks:
        # Find strongest peak
        strongest_peak = max(fitted_peaks, key=lambda x: x['intensity'])
        summary['strongest_peak'] = {
            'two_theta': strongest_peak['two_theta'],
            'd_spacing': strongest_peak['d_spacing'],
            'intensity': strongest_peak['intensity']
        }
        
        # Add all peaks info
        for peak in fitted_peaks:
            summary['peaks'].append({
                'peak_id': peak['peak_id'],
                'two_theta': peak['two_theta'],
                'd_spacing': peak['d_spacing'],
                'intensity': peak['intensity'],
                'fwhm': peak['fwhm']
            })
    else:
        summary['strongest_peak'] = None
        print("No peaks detected. Possible causes:")
        print("- Signal too weak (try lowering --min-height)")
        print("- Data too noisy (try increasing --prominence)")
        print("- Background subtraction removed signal (check your data)")
    
    with open(output_dir / 'summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Analyze XRD patterns')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--wavelength', type=float, default=1.5406, 
                       help='X-ray wavelength in Angstroms')
    parser.add_argument('--min-height', type=float, default=50, 
                       help='Minimum peak height')
    parser.add_argument('--prominence', type=float, default=30, 
                       help='Peak prominence threshold')
    
    args = parser.parse_args()
    
    try:
        # Create output directory
        output_dir = Path(args.output)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data with validation
        data = pd.read_csv(args.input)
        
        # Validate required columns
        if 'two_theta' not in data.columns or 'intensity' not in data.columns:
            raise ValueError("Input file must contain 'two_theta' and 'intensity' columns")
        
        two_theta = data['two_theta'].values
        intensity = data['intensity'].values
        
        # Validate data
        if len(two_theta) < 10:
            raise ValueError("Insufficient data points (minimum 10 required)")
        
        if np.all(intensity <= 0):
            raise ValueError("All intensity values are zero or negative")
        
        # Background subtraction
        background, corrected_intensity = subtract_background(two_theta, intensity)
        
        # Peak detection with adaptive thresholds
        peaks, properties = detect_peaks(two_theta, corrected_intensity, 
                                       args.min_height, args.prominence)
        
        # Gaussian fitting
        fitted_peaks = fit_gaussian_peaks(two_theta, corrected_intensity, peaks)
        
        # Calculate d-spacings
        fitted_peaks = calculate_d_spacings(fitted_peaks, args.wavelength)
        
        # Generate fitted pattern
        fitted_intensity = generate_fitted_pattern(two_theta, fitted_peaks, background)
        
        # Save outputs
        save_outputs(output_dir, two_theta, intensity, background, corrected_intensity,
                    fitted_intensity, fitted_peaks, args.wavelength)
        
        # Results summary
        print(f"Analysis complete: Found {len(fitted_peaks)} peaks")
        if fitted_peaks:
            strongest_peak = max(fitted_peaks, key=lambda x: x['intensity'])
            print(f"Strongest peak at {strongest_peak['two_theta']:.3f}° "
                  f"(d = {strongest_peak['d_spacing']:.3f} Å)")
        
        print(f"Results saved to {output_dir}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
