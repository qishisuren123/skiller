#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
from scipy.signal import lombscargle
import warnings

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze astronomical light curves for periodic variability')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output JSON file')
    parser.add_argument('--min-period', type=float, default=0.1, help='Minimum period in days')
    parser.add_argument('--max-period', type=float, default=100.0, help='Maximum period in days')
    return parser.parse_args()

def calculate_fap(power_max, N_freq, N_data):
    """Calculate false alarm probability using proper statistical method"""
    N_eff = N_freq * 2.0 / N_data if N_data > 0 else N_freq
    fap = 1.0 - (1.0 - np.exp(-power_max))**N_eff
    return min(fap, 1.0)

def find_best_period_with_harmonics(omega, power, times):
    """Find best period considering harmonics to avoid aliasing"""
    peak_indices = []
    for i in range(1, len(power) - 1):
        if power[i] > power[i-1] and power[i] > power[i+1] and power[i] > 0.1:
            peak_indices.append(i)
    
    peak_indices = sorted(peak_indices, key=lambda x: power[x], reverse=True)
    
    if not peak_indices:
        best_idx = np.argmax(power)
        return best_idx, 2 * np.pi / omega[best_idx], power[best_idx]
    
    periods = [2 * np.pi / omega[idx] for idx in peak_indices[:10]]
    powers = [power[idx] for idx in peak_indices[:10]]
    
    best_period = periods[0]
    best_power = powers[0]
    best_idx = peak_indices[0]
    
    for i, period in enumerate(periods):
        harmonic_count = 0
        total_harmonic_power = powers[i]
        
        for j, other_period in enumerate(periods):
            if i != j:
                ratio = period / other_period
                if abs(ratio - round(ratio)) < 0.05:
                    harmonic_count += 1
                    total_harmonic_power += powers[j]
        
        score = total_harmonic_power * (1 + 0.5 * harmonic_count)
        
        if score > best_power * (1 + 0.5 * sum([1 for p in periods if abs((best_period/p) - round(best_period/p)) < 0.05])):
            best_period = period
            best_power = powers[i]
            best_idx = peak_indices[i]
    
    return best_idx, best_period, power[best_idx]

def analyze_light_curve(times, mags, mag_errors, min_period, max_period):
    print(f"  Initial data: times={len(times)}, mags={len(mags)}, errors={len(mag_errors)}")
    
    mask = ~(np.isnan(times) | np.isnan(mags) | np.isnan(mag_errors))
    times_clean = times[mask]
    mags_clean = mags[mask]
    mag_errors_clean = mag_errors[mask]
    
    print(f"  After NaN removal: times={len(times_clean)}, mags={len(mags_clean)}, errors={len(mag_errors_clean)}")
    
    if len(times_clean) < 10:
        return None
    
    sort_idx = np.argsort(times_clean)
    times_sorted = times_clean[sort_idx]
    mags_sorted = mags_clean[sort_idx]
    mag_errors_sorted = mag_errors_clean[sort_idx]
    
    print(f"  After sorting: times={len(times_sorted)}, mags={len(mags_sorted)}, errors={len(mag_errors_sorted)}")
    
    assert len(times_sorted) == len(mags_sorted) == len(mag_errors_sorted), \
        f"Array length mismatch: times={len(times_sorted)}, mags={len(mags_sorted)}, errors={len(mag_errors_sorted)}"
    
    mags_norm = mags_sorted - np.mean(mags_sorted)
    
    time_span = np.max(times_sorted) - np.min(times_sorted)
    dt_median = np.median(np.diff(times_sorted))
    
    min_freq = 1.0 / min(max_period, time_span)
    max_freq = 1.0 / max(min_period, 2 * dt_median)
    
    omega = np.linspace(2 * np.pi * min_freq, 2 * np.pi * max_freq, 8000)
    
    power = lombscargle(times_sorted, mags_norm, omega, normalize=True)
    
    best_idx, best_period, best_power = find_best_period_with_harmonics(omega, power, times_sorted)
    
    fap = calculate_fap(best_power, len(omega), len(times_sorted))
    
    phases = ((times_sorted % best_period) / best_period)
    amplitude = (np.max(mags_sorted) - np.min(mags_sorted)) / 2.0
    
    print(f"  Phase folding: times={len(times_sorted)}, phases={len(phases)}")
    
    phase_bins = np.linspace(0, 1, 10)
    occupied_bins = len(np.unique(np.digitize(phases, phase_bins)))
    phase_coverage = occupied_bins / len(phase_bins)
    
    return {
        'best_period': float(best_period),
        'significance': float(fap),
        'amplitude': float(amplitude),
        'mean_magnitude': float(np.mean(mags_sorted)),
        'n_points': int(len(times_sorted)),
        'phase_coverage': float(phase_coverage)
    }

def main():
    args = parse_arguments()
    
    try:
        data = pd.read_csv(args.input)
        print(f"Loaded {len(data)} data points")
        
        results = {}
        
        for band in data['filter_band'].unique():
            band_data = data[data['filter_band'] == band]
            print(f"Processing band {band} with {len(band_data)} points")
            
            result = analyze_light_curve(
                band_data['time'].values,
                band_data['magnitude'].values,
                band_data['magnitude_error'].values,
                args.min_period,
                args.max_period
            )
            
            if result is not None:
                results[band] = result
                
                significant = result['significance'] < 0.01
                print(f"Band {band}: Period = {result['best_period']:.3f} days, "
                      f"Significant = {significant} (FAP = {result['significance']:.2e})")
            else:
                print(f"Band {band}: Insufficient data for analysis")
        
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == '__main__':
    main()
