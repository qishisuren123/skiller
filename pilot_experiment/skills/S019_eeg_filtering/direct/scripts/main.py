#!/usr/bin/env python3
"""
EEG Signal Filtering and Analysis Tool
Processes multi-channel EEG data with filtering, PSD analysis, and alpha wave detection.
"""

import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy.signal import butter, filtfilt, welch, iirnotch
from pathlib import Path

def apply_bandpass_notch_filter(signal, fs=256):
    """Apply bandpass (0.5-40 Hz) and notch (50 Hz) filters to EEG signal."""
    # Bandpass filter design
    nyquist = fs / 2
    low_cutoff = 0.5 / nyquist
    high_cutoff = 40 / nyquist
    
    # Design 4th order Butterworth bandpass filter
    b_bp, a_bp = butter(4, [low_cutoff, high_cutoff], btype='band')
    
    # Apply bandpass filter (zero-phase)
    filtered_signal = filtfilt(b_bp, a_bp, signal)
    
    # Design and apply notch filter for 50 Hz powerline interference
    b_notch, a_notch = iirnotch(50, Q=30, fs=fs)
    filtered_signal = filtfilt(b_notch, a_notch, filtered_signal)
    
    return filtered_signal

def compute_psd_metrics(signal, fs=256):
    """Compute PSD using Welch's method and extract key metrics."""
    # Compute PSD with Welch's method
    freqs, psd = welch(signal, fs=fs, nperseg=fs, noverlap=fs//2, 
                       window='hann', scaling='density')
    
    # Find dominant frequency
    dominant_freq = freqs[np.argmax(psd)]
    
    # Compute alpha band power ratio (8-13 Hz)
    alpha_mask = (freqs >= 8) & (freqs <= 13)
    alpha_power = np.trapz(psd[alpha_mask], freqs[alpha_mask])
    total_power = np.trapz(psd, freqs)
    alpha_ratio = alpha_power / total_power if total_power > 0 else 0
    
    return freqs, psd, dominant_freq, alpha_ratio, total_power

def analyze_eeg_signals(input_file, output_dir, sample_rate=256):
    """Main EEG analysis pipeline."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Load EEG data
    print(f"Loading EEG data from {input_file}...")
    try:
        data = pd.read_csv(input_file)
    except Exception as e:
        raise ValueError(f"Error loading CSV file: {e}")
    
    # Validate data structure
    expected_columns = ['time'] + [f'ch{i}' for i in range(1, 9)]
    if not all(col in data.columns for col in expected_columns):
        raise ValueError(f"CSV must contain columns: {expected_columns}")
    
    print(f"Loaded {len(data)} samples from {len(data.columns)-1} channels")
    
    # Check for sufficient data length
    duration = len(data) / sample_rate
    if duration < 2:
        print(f"Warning: Short recording duration ({duration:.1f}s). PSD estimates may be unreliable.")
    
    # Initialize results storage
    filtered_data = pd.DataFrame({'time': data['time']})
    psd_results = {}
    summary_stats = {}
    
    # Process each channel
    channel_names = [f'ch{i}' for i in range(1, 9)]
    
    print("Processing channels...")
    for ch_name in channel_names:
        print(f"  Processing {ch_name}...")
        
        # Get channel data and check for missing values
        signal = data[ch_name].values
        if np.any(np.isnan(signal)):
            print(f"    Warning: NaN values detected in {ch_name}, interpolating...")
            signal = pd.Series(signal).interpolate().values
        
        # Apply filtering
        try:
            filtered_signal = apply_bandpass_notch_filter(signal, sample_rate)
            filtered_data[ch_name] = filtered_signal
        except Exception as e:
            raise RuntimeError(f"Error filtering {ch_name}: {e}")
        
        # Compute PSD and metrics
        try:
            freqs, psd, dominant_freq, alpha_ratio, total_power = compute_psd_metrics(
                filtered_signal, sample_rate)
            
            # Store PSD results (first channel sets frequency column)
            if len(psd_results) == 0:
                psd_results['frequency'] = freqs
            psd_results[ch_name] = psd
            
            # Compute additional statistics
            mean_amp = np.mean(np.abs(filtered_signal))
            std_amp = np.std(filtered_signal)
            
            # Store summary statistics
            summary_stats[ch_name] = {
                'dominant_frequency_Hz': float(dominant_freq),
                'alpha_power_ratio': float(alpha_ratio),
                'total_power': float(total_power),
                'mean_amplitude': float(mean_amp),
                'std_amplitude': float(std_amp)
            }
            
        except Exception as e:
            raise RuntimeError(f"Error computing PSD for {ch_name}: {e}")
    
    # Save results
    print("Saving results...")
    
    # Save filtered signals
    filtered_output = os.path.join(output_dir, 'filtered_signals.csv')
    filtered_data.to_csv(filtered_output, index=False)
    print(f"  Filtered signals saved to: {filtered_output}")
    
    # Save PSD data
    psd_df = pd.DataFrame(psd_results)
    psd_output = os.path.join(output_dir, 'psd.csv')
    psd_df.to_csv(psd_output, index=False)
    print(f"  PSD data saved to: {psd_output}")
    
    # Save summary statistics
    summary_output = os.path.join(output_dir, 'summary.json')
    with open(summary_output, 'w') as f:
        json.dump(summary_stats, f, indent=2)
    print(f"  Summary statistics saved to: {summary_output}")
    
    # Display analysis results
    print("\n=== ANALYSIS RESULTS ===")
    print("Dominant frequencies per channel:")
    for ch_name in channel_names:
        freq = summary_stats[ch_name]['dominant_frequency_Hz']
        alpha_ratio = summary_stats[ch_name]['alpha_power_ratio']
        print(f"  {ch_name}: {freq:.1f} Hz (alpha ratio: {alpha_ratio:.3f})")
    
    # Identify channels with strong alpha activity
    strong_alpha_channels = [ch for ch in channel_names 
                           if summary_stats[ch]['alpha_power_ratio'] > 0.2]
    
    print(f"\nChannels with strong alpha activity (ratio > 0.2): {strong_alpha_channels}")
    if not strong_alpha_channels:
        print("No channels show strong alpha activity.")

def main():
    parser = argparse.ArgumentParser(
        description='Filter and analyze multi-channel EEG signals',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument('--input', required=True, 
                       help='Input CSV file path with EEG data')
    parser.add_argument('--output', required=True,
                       help='Output directory for results')
    parser.add_argument('--sample-rate', type=int, default=256,
                       help='Sampling rate in Hz')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input):
        print(f"Error: Input file {args.input} does not exist")
        return 1
    
    if args.sample_rate <= 0:
        print("Error: Sample rate must be positive")
        return 1
    
    try:
        analyze_eeg_signals(args.input, args.output, args.sample_rate)
        print("\nEEG analysis completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
