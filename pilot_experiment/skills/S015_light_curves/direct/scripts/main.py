#!/usr/bin/env python3
"""
Astronomical light curve period detection using Lomb-Scargle periodogram analysis.
"""

import argparse
import json
import numpy as np
import pandas as pd
from scipy.signal import lombscargle
import sys

def compute_periodogram(times, magnitudes, min_period=0.1, max_period=100.0, oversample=5):
    """
    Compute Lomb-Scargle periodogram for given time series.
    
    Args:
        times: Array of observation times (days)
        magnitudes: Array of magnitude measurements
        min_period: Minimum period to search (days)
        max_period: Maximum period to search (days)
        oversample: Oversampling factor for frequency grid
    
    Returns:
        frequencies, power, best_period, best_power, fap
    """
    # Create frequency grid
    df = 1.0 / (max_period - min_period)
    n_freq = int(oversample * (max_period - min_period) / min_period)
    frequencies = np.linspace(1/max_period, 1/min_period, n_freq)
    
    # Compute periodogram
    power = lombscargle(times, magnitudes, 2*np.pi*frequencies, normalize=True)
    
    # Find best period
    best_idx = np.argmax(power)
    best_freq = frequencies[best_idx]
    best_period = 1/best_freq
    best_power = power[best_idx]
    
    # Estimate false alarm probability
    # For normalized Lomb-Scargle: P(power > z) ≈ 1 - (1 - exp(-z))^N
    fap = 1 - (1 - np.exp(-best_power))**len(frequencies)
    
    return frequencies, power, best_period, best_power, fap

def phase_fold_analysis(times, magnitudes, period):
    """
    Phase-fold light curve and compute variability statistics.
    
    Args:
        times: Array of observation times
        magnitudes: Array of magnitude measurements  
        period: Period for phase folding (days)
    
    Returns:
        amplitude, phase_coverage
    """
    # Compute phases
    phases = (times % period) / period
    
    # Calculate amplitude (peak-to-peak in magnitudes)
    amplitude = np.max(magnitudes) - np.min(magnitudes)
    
    # Estimate phase coverage
    phase_bins = np.linspace(0, 1, 21)  # 20 phase bins
    hist, _ = np.histogram(phases, bins=phase_bins)
    phase_coverage = np.sum(hist > 0) / len(hist)
    
    return amplitude, phase_coverage

def analyze_light_curve(df_band, min_period, max_period):
    """
    Analyze single filter band for periodic variability.
    
    Args:
        df_band: DataFrame with time, magnitude, magnitude_error for one band
        min_period: Minimum period to search (days)
        max_period: Maximum period to search (days)
    
    Returns:
        Dictionary with analysis results
    """
    times = df_band['time'].values
    magnitudes = df_band['magnitude'].values
    
    # Check minimum data requirements
    if len(times) < 10:
        return {
            'best_period': None,
            'significance': None,
            'amplitude': None,
            'mean_magnitude': float(np.mean(magnitudes)),
            'n_points': len(times),
            'phase_coverage': None,
            'error': 'Insufficient data points'
        }
    
    try:
        # Compute periodogram
        frequencies, power, best_period, best_power, fap = compute_periodogram(
            times, magnitudes, min_period, max_period
        )
        
        # Phase-fold analysis
        amplitude, phase_coverage = phase_fold_analysis(times, magnitudes, best_period)
        
        return {
            'best_period': float(best_period),
            'significance': float(fap),
            'amplitude': float(amplitude),
            'mean_magnitude': float(np.mean(magnitudes)),
            'n_points': len(times),
            'phase_coverage': float(phase_coverage)
        }
        
    except Exception as e:
        return {
            'best_period': None,
            'significance': None,
            'amplitude': None,
            'mean_magnitude': float(np.mean(magnitudes)),
            'n_points': len(times),
            'phase_coverage': None,
            'error': str(e)
        }

def main():
    parser = argparse.ArgumentParser(
        description='Detect periodic variability in astronomical light curves'
    )
    parser.add_argument('--input', required=True, 
                       help='Input CSV file with light curve data')
    parser.add_argument('--output', required=True,
                       help='Output JSON file for results')
    parser.add_argument('--min-period', type=float, default=0.1,
                       help='Minimum period to search (days)')
    parser.add_argument('--max-period', type=float, default=100.0,
                       help='Maximum period to search (days)')
    
    args = parser.parse_args()
    
    # Load data
    try:
        df = pd.read_csv(args.input)
        required_cols = ['time', 'magnitude', 'magnitude_error', 'filter_band']
        
        if not all(col in df.columns for col in required_cols):
            print(f"Error: CSV must contain columns: {required_cols}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error reading input file: {e}")
        sys.exit(1)
    
    # Analyze each filter band
    results = {}
    significant_detections = []
    
    for band in df['filter_band'].unique():
        print(f"Analyzing filter band: {band}")
        df_band = df[df['filter_band'] == band].copy()
        
        result = analyze_light_curve(df_band, args.min_period, args.max_period)
        results[band] = result
        
        # Check for significant detection
        if (result['significance'] is not None and 
            result['significance'] < 0.01 and
            result['phase_coverage'] is not None and
            result['phase_coverage'] > 0.3):
            
            significant_detections.append({
                'band': band,
                'period': result['best_period'],
                'fap': result['significance']
            })
            
            print(f"  Significant period detected: {result['best_period']:.4f} days "
                  f"(FAP = {result['significance']:.2e})")
        else:
            print(f"  No significant variability detected")
    
    # Save results
    try:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to {args.output}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)
    
    # Summary
    print(f"\nSummary:")
    print(f"Total filter bands analyzed: {len(results)}")
    print(f"Significant detections (FAP < 0.01): {len(significant_detections)}")
    
    for detection in significant_detections:
        print(f"  {detection['band']}: P = {detection['period']:.4f} days")

if __name__ == '__main__':
    main()
