#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import json
import os
from scipy import signal
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_signal(data):
    """Clean signal by handling NaN values and outliers"""
    # Replace NaN with interpolated values
    if np.any(np.isnan(data)):
        logging.warning("Found NaN values in signal, interpolating...")
        mask = np.isnan(data)
        data[mask] = np.interp(np.flatnonzero(mask), np.flatnonzero(~mask), data[~mask])
    
    # Remove extreme outliers (beyond 5 standard deviations)
    std_thresh = 5 * np.std(data)
    mean_val = np.mean(data)
    outlier_mask = np.abs(data - mean_val) > std_thresh
    if np.any(outlier_mask):
        logging.warning(f"Found {np.sum(outlier_mask)} outliers, clipping...")
        data[outlier_mask] = np.clip(data[outlier_mask], mean_val - std_thresh, mean_val + std_thresh)
    
    return data

def apply_bandpass_filter(data, lowcut=0.5, highcut=40, fs=256, order=4):
    """Apply Butterworth bandpass filter"""
    nyquist = 0.5 * fs
    low = lowcut / nyquist
    high = highcut / nyquist
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)

def apply_notch_filter(data, freq=50, fs=256, quality=30):
    """Apply notch filter to remove powerline interference"""
    b, a = signal.iirnotch(freq, quality, fs)
    return signal.filtfilt(b, a, data)

def compute_psd(data, fs=256, nperseg=2048):
    """Compute power spectral density using Welch's method"""
    # Ensure data is float64 to avoid dtype issues
    data = np.asarray(data, dtype=np.float64)
    freqs, psd = signal.welch(data, fs, nperseg=nperseg, noverlap=nperseg//2)
    return freqs, psd

def analyze_alpha_waves(freqs, psd):
    """Compute alpha wave ratio (8-13 Hz)"""
    # Focus on relevant frequency range for EEG analysis (0.5-40 Hz)
    analysis_mask = (freqs >= 0.5) & (freqs <= 40)
    analysis_freqs = freqs[analysis_mask]
    analysis_psd = psd[analysis_mask]
    
    # Alpha band (8-13 Hz)
    alpha_mask = (analysis_freqs >= 8) & (analysis_freqs <= 13)
    alpha_power = np.trapz(analysis_psd[alpha_mask], analysis_freqs[alpha_mask])
    
    # Total power in analysis range
    total_power = np.trapz(analysis_psd, analysis_freqs)
    
    return alpha_power / total_power if total_power > 0 else 0

def process_channel_chunk(chunk_data, fs, filter_coeffs):
    """Process a single chunk of channel data"""
    # Apply pre-computed filter coefficients
    bp_b, bp_a, notch_b, notch_a = filter_coeffs
    
    # Clean signal
    clean_data = clean_signal(chunk_data.copy())
    
    # Apply filters
    bandpass_filtered = signal.filtfilt(bp_b, bp_a, clean_data)
    fully_filtered = signal.filtfilt(notch_b, notch_a, bandpass_filtered)
    
    return fully_filtered

def process_eeg_data(input_file, output_dir, sample_rate):
    """Main processing function with chunked processing"""
    logging.info(f"Loading data from {input_file}")
    
    try:
        # Load data in chunks to save memory
        chunk_size = 50000  # Process 50k samples at a time (~3 minutes at 256 Hz)
        
        # First pass: get data info
        df_info = pd.read_csv(input_file, nrows=1)
        channels = [f'ch{i}' for i in range(1, 9)]
        
        # Get total number of rows
        total_rows = sum(1 for line in open(input_file)) - 1  # subtract header
        logging.info(f"Processing {total_rows} samples in chunks of {chunk_size}")
        
        # Pre-compute filter coefficients
        nyquist = 0.5 * sample_rate
        low = 0.5 / nyquist
        high = 40 / nyquist
        bp_b, bp_a = signal.butter(4, [low, high], btype='band')
        notch_b, notch_a = signal.iirnotch(50, 30, sample_rate)
        filter_coeffs = (bp_b, bp_a, notch_b, notch_a)
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Initialize output files
        filtered_output_path = os.path.join(output_dir, 'filtered_signals.csv')
        
        # Process data in chunks
        summary_data = {}
        all_psds = {}
        reference_freqs = None
        
        first_chunk = True
        chunk_num = 0
        
        for chunk_df in pd.read_csv(input_file, chunksize=chunk_size):
            chunk_num += 1
            logging.info(f"Processing chunk {chunk_num}/{(total_rows//chunk_size)+1}")
            
            time = chunk_df['time'].values
            chunk_filtered = {'time': time}
            
            for ch in channels:
                raw_signal = chunk_df[ch].values
                filtered_signal = process_channel_chunk(raw_signal, sample_rate, filter_coeffs)
                chunk_filtered[ch] = filtered_signal
                
                # Accumulate data for PSD computation (only keep every 10th sample to save memory)
                if ch not in all_psds:
                    all_psds[ch] = []
                all_psds[ch].extend(filtered_signal[::10].tolist())  # Convert to list to avoid dtype issues
            
            # Write filtered data chunk
            chunk_filtered_df = pd.DataFrame(chunk_filtered)
            if first_chunk:
                chunk_filtered_df.to_csv(filtered_output_path, index=False, mode='w')
                first_chunk = False
            else:
                chunk_filtered_df.to_csv(filtered_output_path, index=False, mode='a', header=False)
        
        logging.info("Computing PSD and summary statistics...")
        
        # Compute PSD on accumulated data
        psd_data = {}
        
        for ch in channels:
            logging.info(f"Computing PSD for {ch}")
            
            # Convert accumulated data to numpy array with explicit dtype
            channel_data = np.array(all_psds[ch], dtype=np.float64)
            
            # Compute PSD (using downsampled rate)
            downsample_fs = sample_rate // 10
            nperseg = min(2048, len(channel_data)//4)
            freqs, psd = compute_psd(channel_data, fs=downsample_fs, nperseg=nperseg)
            
            if reference_freqs is None:
                reference_freqs = freqs
                psd_data['frequency'] = freqs
            
            psd_data[ch] = psd
            
            # Analysis
            alpha_ratio = analyze_alpha_waves(freqs, psd)
            dominant_freq = freqs[np.argmax(psd)]
            
            # Compute total power in EEG range (0.5-40 Hz)
            eeg_mask = (freqs >= 0.5) & (freqs <= 40)
            total_power = np.trapz(psd[eeg_mask], freqs[eeg_mask])
            
            summary_data[ch] = {
                'dominant_frequency_Hz': float(dominant_freq),
                'alpha_power_ratio': float(alpha_ratio),
                'total_power': float(total_power),
                'mean_amplitude': float(np.mean(channel_data)),
                'std_amplitude': float(np.std(channel_data))
            }
        
        # Save PSD and summary
        logging.info("Saving PSD data...")
        psd_df = pd.DataFrame(psd_data)
        psd_output_path = os.path.join(output_dir, 'psd.csv')
        psd_df.to_csv(psd_output_path, index=False)
        
        logging.info("Saving summary...")
        summary_output_path = os.path.join(output_dir, 'summary.json')
        with open(summary_output_path, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        # Print results
        print("Dominant frequencies per channel:")
        for ch in channels:
            print(f"{ch}: {summary_data[ch]['dominant_frequency_Hz']:.2f} Hz")
        
        print("\nChannels with strong alpha activity (ratio > 0.2):")
        alpha_channels = []
        for ch in channels:
            if summary_data[ch]['alpha_power_ratio'] > 0.2:
                alpha_channels.append(f"{ch}: {summary_data[ch]['alpha_power_ratio']:.3f}")
        
        if alpha_channels:
            for ch_info in alpha_channels:
                print(ch_info)
        else:
            print("No channels with strong alpha activity found.")
            
    except Exception as e:
        logging.error(f"Error processing EEG data: {str(e)}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Filter and analyze multi-channel EEG signals')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--sample-rate', type=int, default=256, help='Sampling rate in Hz')
    
    args = parser.parse_args()
    
    setup_logging()
    process_eeg_data(args.input, args.output, args.sample_rate)

if __name__ == '__main__':
    main()
