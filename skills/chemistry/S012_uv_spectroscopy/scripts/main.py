#!/usr/bin/env python3
import argparse
import json
import pandas as pd
import numpy as np
from scipy.signal import find_peaks, peak_widths
from scipy.integrate import trapz
import logging

def setup_logging(verbosity):
    """Setup logging configuration"""
    levels = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG
    }
    level = levels.get(verbosity, logging.DEBUG)
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

def detect_peaks(wavelength, absorbance, min_height=0.1, min_distance=10):
    """Detect peaks in UV-Vis absorption data"""
    logger = logging.getLogger(__name__)
    
    # Convert min_distance from nm to index points
    wl_spacing = np.mean(np.diff(wavelength))
    min_distance_idx = int(min_distance / wl_spacing)
    
    logger.debug(f"Wavelength spacing: {wl_spacing:.2f} nm, min_distance_idx: {min_distance_idx}")
    
    # Find peaks using prominence
    peaks, properties = find_peaks(absorbance, 
                                 height=min_height,
                                 distance=min_distance_idx,
                                 prominence=min_height/2)
    
    logger.info(f"Found {len(peaks)} peaks with min_height={min_height}")
    
    # Ensure peaks is a proper 1-D numpy array
    peaks = np.asarray(peaks).flatten()
    logger.debug(f"Peaks array shape: {peaks.shape}, dtype: {peaks.dtype}")
    
    peak_data = []
    if len(peaks) > 0:
        try:
            # Calculate FWHM for all peaks at once
            widths, width_heights, left_ips, right_ips = peak_widths(
                absorbance, peaks, rel_height=0.5)
            
            for i, peak_idx in enumerate(peaks):
                # Skip peaks with zero or very small width (noise spikes)
                if widths[i] < 0.5:  # Less than 0.5 data points wide
                    logger.debug(f"Skipping peak {i+1} with zero/small width: {widths[i]}")
                    continue
                    
                peak_wl = wavelength[peak_idx]
                peak_height = absorbance[peak_idx]
                fwhm = widths[i] * wl_spacing
                
                # Calculate area by integration around peak with baseline correction
                left_idx = max(0, int(left_ips[i]))
                right_idx = min(len(absorbance), int(right_ips[i]) + 1)
                
                # Extract peak region
                peak_wavelengths = wavelength[left_idx:right_idx]
                peak_absorbances = absorbance[left_idx:right_idx]
                
                # Calculate baseline as linear interpolation between endpoints
                baseline_start = peak_absorbances[0]
                baseline_end = peak_absorbances[-1]
                baseline = np.linspace(baseline_start, baseline_end, len(peak_absorbances))
                
                # Subtract baseline and integrate
                corrected_absorbance = peak_absorbances - baseline
                area = trapz(corrected_absorbance, peak_wavelengths)
                
                logger.debug(f"Peak {i+1}: λ={peak_wl:.1f}nm, h={peak_height:.3f}, "
                            f"FWHM={fwhm:.1f}nm, area={area:.3f}")
                
                peak_data.append({
                    'wavelength': float(peak_wl),
                    'height': float(peak_height),
                    'fwhm': float(fwhm),
                    'area': float(area)
                })
                
        except Exception as e:
            logger.error(f"Error in peak_widths calculation: {str(e)}")
            logger.error(f"Peaks array: {peaks}")
            logger.error(f"Absorbance shape: {absorbance.shape}")
            raise
    
    return peak_data

def analyze_sample(sample_name, wavelength, absorbance, min_height, min_distance):
    """Analyze peaks for a single sample"""
    logger = logging.getLogger(__name__)
    logger.info(f"Processing sample: {sample_name}")
    
    # Check for data quality issues
    if np.any(np.isnan(absorbance)):
        logger.warning(f"Sample {sample_name} contains NaN values")
    if np.any(absorbance < 0):
        logger.warning(f"Sample {sample_name} contains negative absorbance values")
    
    peaks = detect_peaks(wavelength, absorbance, min_height, min_distance)
    
    dominant_peak = None
    if peaks:
        dominant_peak = max(peaks, key=lambda x: x['height'])
        logger.info(f"Sample {sample_name}: dominant peak at {dominant_peak['wavelength']:.1f}nm "
                   f"(height: {dominant_peak['height']:.3f})")
    else:
        logger.warning(f"No peaks found in sample {sample_name}")
    
    return {
        'peaks': peaks,
        'dominant_peak': dominant_peak,
        'n_peaks': len(peaks)
    }

def main():
    parser = argparse.ArgumentParser(description='Analyze UV-Vis absorption peaks')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--min-height', type=float, default=0.1, 
                       help='Minimum peak height (default: 0.1)')
    parser.add_argument('--min-distance', type=float, default=10.0,
                       help='Minimum distance between peaks in nm (default: 10)')
    parser.add_argument('-v', '--verbose', action='count', default=0,
                       help='Increase verbosity (-v for INFO, -vv for DEBUG)')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting UV-Vis peak analysis")
    logger.info(f"Input file: {args.input}")
    logger.info(f"Parameters: min_height={args.min_height}, min_distance={args.min_distance}nm")
    
    try:
        # Load data with explicit numeric conversion
        logger.info("Loading CSV data...")
        df = pd.read_csv(args.input)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Convert to numeric, coercing errors to NaN
        for col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Drop rows with NaN values
        rows_before = len(df)
        df = df.dropna()
        if len(df) < rows_before:
            logger.warning(f"Dropped {rows_before - len(df)} rows containing NaN values")
        
        wavelength = df['wavelength'].values.astype(float)
        logger.info(f"Wavelength range: {wavelength.min():.1f} - {wavelength.max():.1f} nm")
        
        results = {}
        
        # Process each sample column
        sample_columns = [col for col in df.columns if col != 'wavelength']
        logger.info(f"Found {len(sample_columns)} sample columns: {sample_columns}")
        
        for sample_col in sample_columns:
            absorbance = df[sample_col].values.astype(float)
            results[sample_col] = analyze_sample(sample_col, wavelength, absorbance, 
                                               args.min_height, args.min_distance)
        
        # Save results
        logger.info(f"Saving results to {args.output}")
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        print(f"Analysis complete for {len(sample_columns)} samples:")
        dominant_wavelengths = []
        
        for sample, data in results.items():
            print(f"  {sample}: {data['n_peaks']} peaks")
            if data['dominant_peak']:
                dominant_wavelengths.append(data['dominant_peak']['wavelength'])
        
        if dominant_wavelengths:
            wl_range = f"{min(dominant_wavelengths):.1f}-{max(dominant_wavelengths):.1f} nm"
            print(f"Dominant peak wavelength range: {wl_range}")
        
        logger.info("Analysis completed successfully")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()
