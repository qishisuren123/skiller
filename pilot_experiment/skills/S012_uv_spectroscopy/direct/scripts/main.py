import argparse
import pandas as pd
import numpy as np
import json
from scipy.signal import find_peaks, peak_widths

def detect_peaks(wavelength, absorbance, min_height, min_distance_nm):
    """Detect peaks in UV-Vis absorption spectrum and calculate properties."""
    # Calculate wavelength spacing for distance conversion
    wavelength_spacing = np.mean(np.diff(wavelength))
    min_distance_points = int(min_distance_nm / wavelength_spacing)
    
    # Find peaks using prominence-based detection
    peaks, properties = find_peaks(absorbance, 
                                  height=min_height,
                                  distance=min_distance_points)
    
    if len(peaks) == 0:
        return []
    
    # Calculate peak widths (FWHM)
    widths = peak_widths(absorbance, peaks, rel_height=0.5)
    fwhm_nm = widths[0] * wavelength_spacing
    
    # Calculate peak areas by integration
    peak_data = []
    for i, peak_idx in enumerate(peaks):
        # Define integration bounds from width calculation
        left_idx = int(widths[2][i])
        right_idx = int(widths[3][i])
        
        # Ensure bounds are within array limits
        left_idx = max(0, left_idx)
        right_idx = min(len(wavelength), right_idx)
        
        # Integrate peak area
        if right_idx > left_idx:
            area = np.trapz(absorbance[left_idx:right_idx], 
                           wavelength[left_idx:right_idx])
        else:
            area = 0.0
        
        peak_data.append({
            'wavelength': float(wavelength[peak_idx]),
            'height': float(absorbance[peak_idx]),
            'fwhm': float(fwhm_nm[i]),
            'area': float(area)
        })
    
    return peak_data

def analyze_sample(wavelength, absorbance, min_height, min_distance):
    """Analyze a single sample for peaks and dominant peak."""
    # Remove NaN values
    mask = ~np.isnan(absorbance)
    clean_wavelength = wavelength[mask]
    clean_absorbance = absorbance[mask]
    
    if len(clean_absorbance) == 0:
        return {'peaks': [], 'dominant_peak': None, 'n_peaks': 0}
    
    # Detect peaks
    peaks = detect_peaks(clean_wavelength, clean_absorbance, min_height, min_distance)
    
    # Find dominant peak (highest absorbance)
    dominant_peak = None
    if peaks:
        dominant_peak = max(peaks, key=lambda x: x['height'])
    
    return {
        'peaks': peaks,
        'dominant_peak': dominant_peak,
        'n_peaks': len(peaks)
    }

def main():
    parser = argparse.ArgumentParser(description='Detect and analyze peaks in UV-Vis absorption spectroscopy data')
    parser.add_argument('--input', required=True, help='Input CSV file with wavelength and absorbance data')
    parser.add_argument('--output', required=True, help='Output JSON file for results')
    parser.add_argument('--min-height', type=float, default=0.1, help='Minimum peak height (default: 0.1)')
    parser.add_argument('--min-distance', type=float, default=10.0, help='Minimum distance between peaks in nm (default: 10)')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = pd.read_csv(args.input)
        
        # Validate required columns
        if 'wavelength' not in df.columns:
            raise ValueError("CSV must contain 'wavelength' column")
        
        wavelength = df['wavelength'].values
        
        # Check wavelength is monotonically increasing
        if not np.all(np.diff(wavelength) > 0):
            raise ValueError("Wavelength data must be monotonically increasing")
        
        # Find sample columns (all columns except wavelength)
        sample_columns = [col for col in df.columns if col != 'wavelength']
        
        if not sample_columns:
            raise ValueError("No sample columns found in CSV")
        
        # Analyze each sample
        results = {}
        dominant_wavelengths = []
        
        for sample_col in sample_columns:
            absorbance = df[sample_col].values
            sample_result = analyze_sample(wavelength, absorbance, args.min_height, args.min_distance)
            results[sample_col] = sample_result
            
            if sample_result['dominant_peak']:
                dominant_wavelengths.append(sample_result['dominant_peak']['wavelength'])
        
        # Save results to JSON
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print("UV-Vis Peak Analysis Summary")
        print("=" * 40)
        for sample_name, data in results.items():
            print(f"{sample_name}: {data['n_peaks']} peaks detected")
        
        if dominant_wavelengths:
            print(f"\nDominant peak wavelength range: {min(dominant_wavelengths):.1f} - {max(dominant_wavelengths):.1f} nm")
        else:
            print("\nNo dominant peaks found in any sample")
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
