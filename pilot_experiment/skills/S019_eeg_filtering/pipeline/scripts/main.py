#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
from scipy import signal
from pathlib import Path
import sys

def parse_arguments():
    parser = argparse.ArgumentParser(description='Filter and analyze multi-channel EEG signals')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--sample-rate', type=int, default=256, help='Sampling rate in Hz')
    return parser.parse_args()

def validate_input_data(data):
    """Validate that input CSV has the expected structure"""
    required_columns = ['time'] + [f'ch{i}' for i in range(1, 9)]
    
    # Check if all required columns exist
    missing_columns = [col for col in required_columns if col not in data.columns]
    if missing_columns:
        print(f"Error: Missing required columns: {missing_columns}")
        print(f"Expected columns: {required_columns}")
        print(f"Found columns: {list(data.columns)}")
        return False
    
    # Check for non-numeric data in channel columns
    for col in required_columns[1:]:  # Skip 'time' column
        if not pd.api.types.is_numeric_dtype(data[col]):
            print(f"Error: Column {col} contains non-numeric data")
            return False
    
    # Check for reasonable data ranges (EEG typically -200 to +200 microvolts)
    for col in required_columns[1:]:
        col_range = data[col].max() - data[col].min()
        if col_range == 0:
            print(f"Warning: Column {col} has constant values")
        elif col_range > 1000:
            print(f"Warning: Column {col} has unusually large range ({col_range:.1f}). Are units correct?")
    
    # Check time column
    if not pd.api.types.is_numeric_dtype(data['time']):
        print("Error: Time column contains non-numeric data")
        return False
    
    print(f"Input validation passed: {len(data)} samples, {len(required_columns)} channels")
    return True

def apply_filters(data, sample_rate):
    """Apply bandpass and notch filters to EEG data"""
    filtered_data = data.copy()
    
    # Check minimum length requirement
    min_length = 100
    if len(data) < min_length:
        print(f"Warning: Signal too short ({len(data)} samples). Minimum recommended: {min_length}")
        return filtered_data
    
    # Bandpass filter (0.5-40 Hz)
    nyquist = sample_rate / 2
    low = 0.5 / nyquist
    high = 40 / nyquist
    
    filter_order = min(4, len(data) // 30)
    b, a = signal.butter(filter_order, [low, high], btype='band')
    
    # Notch filter (50 Hz) - only apply if sample rate allows
    if sample_rate > 100:
        notch_freq = 50 / nyquist
        bn, an = signal.iirnotch(notch_freq, Q=30)
    else:
        bn, an = None, None
    
    # Apply filters to each channel
    for col in data.columns:
        if col != 'time':
            try:
                # Apply bandpass filter
                filtered_data[col] = signal.filtfilt(b, a, data[col])
                # Apply notch filter if applicable
                if bn is not None:
                    filtered_data[col] = signal.filtfilt(bn, an, filtered_data[col])
            except ValueError as e:
                print(f"Warning: Could not filter channel {col}: {e}")
                filtered_data[col] = data[col]
    
    return filtered_data

def compute_psd(data, sample_rate):
    """Compute power spectral density using Welch's method"""
    psd_results = {}
    
    for col in data.columns:
        if col != 'time':
            # Adjust nperseg for better frequency resolution
            nperseg = min(1024, len(data) // 4)
            noverlap = nperseg // 2
            
            freqs, psd = signal.welch(data[col], fs=sample_rate, 
                                    nperseg=nperseg, noverlap=noverlap,
                                    detrend='constant')
            
            if 'frequency' not in psd_results:
                psd_results['frequency'] = freqs
            psd_results[col] = psd
    
    return pd.DataFrame(psd_results)

def convert_numpy_types(obj):
    """Convert numpy types to native Python types for JSON serialization"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    else:
        return obj

def analyze_channels(data, psd_df, sample_rate):
    """Analyze each channel for alpha waves and other metrics"""
    results = {}
    
    for col in data.columns:
        if col != 'time':
            # Get PSD data for this channel
            freqs = psd_df['frequency'].values
            psd_values = psd_df[col].values
            
            # Focus on relevant frequency range (1-40 Hz) for dominant frequency
            relevant_mask = (freqs >= 1.0) & (freqs <= 40.0)
            if np.any(relevant_mask):
                relevant_freqs = freqs[relevant_mask]
                relevant_psd = psd_values[relevant_mask]
                dominant_idx = np.argmax(relevant_psd)
                dominant_freq = relevant_freqs[dominant_idx]
            else:
                dominant_freq = 0.0
            
            # Calculate alpha band power (8-13 Hz)
            alpha_mask = (freqs >= 8) & (freqs <= 13)
            total_mask = (freqs >= 1.0) & (freqs <= 40.0)
            
            if np.any(alpha_mask) and np.any(total_mask):
                alpha_power = np.trapz(psd_values[alpha_mask], freqs[alpha_mask])
                total_power = np.trapz(psd_values[total_mask], freqs[total_mask])
                alpha_ratio = alpha_power / total_power if total_power > 0 else 0.0
            else:
                alpha_power = 0.0
                total_power = np.trapz(psd_values, freqs)
                alpha_ratio = 0.0
            
            # Signal statistics
            mean_amp = np.mean(data[col])
            std_amp = np.std(data[col])
            
            # Store results with explicit type conversion
            results[col] = {
                'dominant_frequency_Hz': float(dominant_freq),
                'alpha_power_ratio': float(alpha_ratio),
                'total_power': float(total_power),
                'mean_amplitude': float(mean_amp),
                'std_amplitude': float(std_amp)
            }
    
    return results

def main():
    args = parse_arguments()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    try:
        # Load data
        data = pd.read_csv(args.input)
        print(f"Loaded data: {len(data)} samples, {len(data.columns)} columns")
        
        # Validate input structure
        if not validate_input_data(data):
            sys.exit(1)
        
    except Exception as e:
        print(f"Error loading input file: {e}")
        sys.exit(1)
    
    # Apply filters
    filtered_data = apply_filters(data, args.sample_rate)
    
    # Compute PSD
    psd_df = compute_psd(filtered_data, args.sample_rate)
    
    # Analyze channels
    analysis = analyze_channels(filtered_data, psd_df, args.sample_rate)
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Save results
        filtered_data.to_csv(output_dir / 'filtered_signals.csv', index=False)
        psd_df.to_csv(output_dir / 'psd.csv', index=False)
        
        # Convert numpy types before JSON serialization
        analysis_serializable = convert_numpy_types(analysis)
        with open(output_dir / 'summary.json', 'w') as f:
            json.dump(analysis_serializable, f, indent=2)
            
        print(f"Results saved to {output_dir}")
        
    except Exception as e:
        print(f"Error saving results: {e}")
        sys.exit(1)
    
    # Print results
    print("\nDominant frequencies per channel:")
    for ch, ch_data in analysis.items():
        print(f"{ch}: {ch_data['dominant_frequency_Hz']:.2f} Hz")
    
    print("\nChannels with strong alpha activity (ratio > 0.2):")
    alpha_channels = []
    for ch, ch_data in analysis.items():
        if ch_data['alpha_power_ratio'] > 0.2:
            alpha_channels.append(f"{ch}: {ch_data['alpha_power_ratio']:.3f}")
    
    if alpha_channels:
        for ch_info in alpha_channels:
            print(ch_info)
    else:
        print("No channels with strong alpha activity found")

if __name__ == "__main__":
    main()
