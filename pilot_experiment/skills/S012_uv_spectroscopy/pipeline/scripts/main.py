import argparse
import pandas as pd
import numpy as np
import json
from scipy.signal import find_peaks, peak_widths, savgol_filter
from scipy.integrate import trapz

def smooth_data(absorbance, method='savgol', window_length=5, polyorder=2):
    """Apply smoothing to reduce noise"""
    if method == 'savgol':
        # Ensure window_length is odd and reasonable
        window_length = max(3, window_length)
        if window_length % 2 == 0:
            window_length += 1
        window_length = min(window_length, len(absorbance) // 2)
        polyorder = min(polyorder, window_length - 1)
        
        return savgol_filter(absorbance, window_length, polyorder)
    elif method == 'moving_average':
        # Simple moving average
        window = np.ones(window_length) / window_length
        return np.convolve(absorbance, window, mode='same')
    else:
        return absorbance

def validate_data(wavelength, absorbance, sample_name):
    """Validate UV-Vis data and return warnings"""
    warnings = []
    
    # Check for NaN or infinite values
    if np.any(np.isnan(wavelength)) or np.any(np.isnan(absorbance)):
        warnings.append(f"{sample_name}: Contains NaN values")
    if np.any(np.isinf(absorbance)):
        warnings.append(f"{sample_name}: Contains infinite absorbance values")
    
    # Check wavelength ordering and spacing
    if not np.all(np.diff(wavelength) > 0):
        warnings.append(f"{sample_name}: Wavelength data is not monotonically increasing")
    
    wl_diffs = np.diff(wavelength)
    if len(wl_diffs) > 0 and np.std(wl_diffs) / np.mean(wl_diffs) > 0.1:
        warnings.append(f"{sample_name}: Irregular wavelength spacing detected")
    
    # Check for negative absorbance (unusual but possible)
    if np.any(absorbance < -0.1):
        warnings.append(f"{sample_name}: Significant negative absorbance values detected")
    
    # Check for very high absorbance (>3 is often unreliable)
    if np.any(absorbance > 3.0):
        warnings.append(f"{sample_name}: Very high absorbance values (>3.0) detected")
    
    # Check data length
    if len(wavelength) < 10:
        warnings.append(f"{sample_name}: Very few data points ({len(wavelength)})")
    
    return warnings

def analyze_peaks(wavelength, absorbance, min_height, min_distance, smooth_method=None, smooth_window=5):
    """Analyze peaks in UV-Vis spectrum with improved noise handling"""
    
    # Apply smoothing if requested
    if smooth_method:
        smoothed_absorbance = smooth_data(absorbance, smooth_method, smooth_window)
    else:
        smoothed_absorbance = absorbance
    
    # Convert min_distance from nm to array indices
    wl_spacing = np.mean(np.diff(wavelength))
    min_distance_idx = max(1, int(min_distance / wl_spacing))
    
    # Calculate adaptive prominence based on noise level
    noise_level = np.std(np.diff(smoothed_absorbance))  # Estimate noise from derivatives
    min_prominence = max(0.01, noise_level * 3)  # 3x noise level
    
    # Find peaks with more stringent criteria
    peaks, properties = find_peaks(smoothed_absorbance, 
                                 height=min_height,
                                 distance=min_distance_idx,
                                 prominence=min_prominence,
                                 width=2)  # Require minimum width
    
    if len(peaks) == 0:
        return []
    
    # Calculate peak widths at half maximum
    try:
        widths, width_heights, left_ips, right_ips = peak_widths(smoothed_absorbance, peaks, rel_height=0.5)
    except Exception:
        # Fallback if peak_widths fails
        return []
    
    peak_data = []
    for i, peak_idx in enumerate(peaks):
        # Use original (unsmoothed) data for measurements
        peak_wl = wavelength[peak_idx]
        peak_height = absorbance[peak_idx]  # Use original absorbance for height
        
        # Convert width from indices to wavelength units
        fwhm = widths[i] * wl_spacing
        
        # Skip peaks that are too narrow (likely noise)
        if fwhm < wl_spacing * 2:  # Less than 2 data points wide
            continue
            
        # Calculate area under peak with baseline correction
        left_idx = int(left_ips[i])
        right_idx = int(right_ips[i]) + 1
        
        # Ensure indices are within bounds
        left_idx = max(0, left_idx)
        right_idx = min(len(absorbance), right_idx)
        
        # Extract peak region
        peak_wavelengths = wavelength[left_idx:right_idx]
        peak_absorbances = absorbance[left_idx:right_idx]
        
        # Calculate baseline (linear interpolation between endpoints)
        if len(peak_absorbances) > 1:
            baseline_left = absorbance[left_idx]
            baseline_right = absorbance[right_idx-1]
            baseline = np.linspace(baseline_left, baseline_right, len(peak_absorbances))
            
            # Subtract baseline and integrate
            corrected_absorbances = peak_absorbances - baseline
            area = trapz(corrected_absorbances, peak_wavelengths)
        else:
            area = 0.0  # Single point peak
        
        peak_data.append({
            'wavelength': float(peak_wl),
            'height': float(peak_height),
            'fwhm': float(fwhm),
            'area': float(area)
        })
    
    return peak_data

def main():
    parser = argparse.ArgumentParser(description='Analyze UV-Vis spectroscopy peaks')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--min-height', type=float, default=0.1, help='Minimum peak height')
    parser.add_argument('--min-distance', type=float, default=10.0, help='Minimum distance between peaks (nm)')
    parser.add_argument('--smooth', choices=['savgol', 'moving_average'], help='Smoothing method')
    parser.add_argument('--smooth-window', type=int, default=5, help='Smoothing window size')
    
    args = parser.parse_args()
    
    # Load data
    try:
        df = pd.read_csv(args.input)
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return
    
    if 'wavelength' not in df.columns:
        print("Error: 'wavelength' column not found in CSV file")
        return
    
    wavelength = df['wavelength'].values
    
    # Find sample columns - exclude wavelength column
    sample_columns = [col for col in df.columns if col.lower() != 'wavelength']
    
    if not sample_columns:
        print("Error: No sample columns found in the CSV file")
        return
    
    results = {}
    all_warnings = []
    dominant_wavelengths = []
    
    for col in sample_columns:
        absorbance = df[col].values
        
        # Validate data
        warnings = validate_data(wavelength, absorbance, col)
        all_warnings.extend(warnings)
        
        peaks = analyze_peaks(wavelength, absorbance, args.min_height, args.min_distance, 
                            args.smooth, args.smooth_window)
        
        # Find dominant peak - handle empty peaks list
        dominant_peak = max(peaks, key=lambda x: x['height']) if peaks else None
        if dominant_peak:
            dominant_wavelengths.append(dominant_peak['wavelength'])
        
        results[col] = {
            'peaks': peaks,
            'dominant_peak': dominant_peak,
            'n_peaks': len(peaks)
        }
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print warnings
    if all_warnings:
        print("Data validation warnings:")
        for warning in all_warnings:
            print(f"  - {warning}")
        print()
    
    # Print summary
    print("Peak Analysis Summary:")
    for sample, data in results.items():
        print(f"{sample}: {data['n_peaks']} peaks")
        if data['dominant_peak']:
            print(f"  Dominant peak at {data['dominant_peak']['wavelength']:.1f} nm")
    
    # Print dominant peak wavelength range
    if dominant_wavelengths:
        min_wl = min(dominant_wavelengths)
        max_wl = max(dominant_wavelengths)
        print(f"\nDominant peak wavelength range: {min_wl:.1f} - {max_wl:.1f} nm")
    else:
        print("\nNo dominant peaks found across all samples")

if __name__ == '__main__':
    main()
