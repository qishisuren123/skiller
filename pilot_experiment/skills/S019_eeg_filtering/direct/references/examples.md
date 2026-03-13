# Example 1: Basic EEG filtering workflow
import pandas as pd
import numpy as np
from scipy.signal import butter, filtfilt, welch, iirnotch

# Load sample EEG data
data = pd.read_csv('eeg_sample.csv')  # time, ch1, ch2, ..., ch8
fs = 256  # Hz

# Process single channel
signal = data['ch1'].values

# Design and apply bandpass filter (0.5-40 Hz)
nyquist = fs / 2
b_bp, a_bp = butter(4, [0.5/nyquist, 40/nyquist], btype='band')
filtered = filtfilt(b_bp, a_bp, signal)

# Apply notch filter (50 Hz powerline)
b_notch, a_notch = iirnotch(50, Q=30, fs=fs)
filtered = filtfilt(b_notch, a_notch, filtered)

# Compute PSD with Welch's method
freqs, psd = welch(filtered, fs=fs, nperseg=256, noverlap=128)

# Calculate alpha band power ratio
alpha_mask = (freqs >= 8) & (freqs <= 13)
alpha_power = np.trapz(psd[alpha_mask], freqs[alpha_mask])
total_power = np.trapz(psd, freqs)
alpha_ratio = alpha_power / total_power

print(f"Alpha power ratio: {alpha_ratio:.3f}")
print(f"Dominant frequency: {freqs[np.argmax(psd)]:.1f} Hz")

# Example 2: Complete multi-channel analysis with error handling
def process_eeg_file(filename, output_dir):
    try:
        # Load and validate data
        data = pd.read_csv(filename)
        channels = [f'ch{i}' for i in range(1, 9)]
        
        if not all(ch in data.columns for ch in channels):
            raise ValueError("Missing required channels")
        
        results = {}
        fs = 256
        
        for ch in channels:
            signal = data[ch].values
            
            # Handle missing values
            if np.any(np.isnan(signal)):
                signal = pd.Series(signal).interpolate().values
            
            # Apply filters
            nyquist = fs / 2
            b_bp, a_bp = butter(4, [0.5/nyquist, 40/nyquist], btype='band')
            filtered = filtfilt(b_bp, a_bp, signal)
            
            b_notch, a_notch = iirnotch(50, Q=30, fs=fs)
            filtered = filtfilt(b_notch, a_notch, filtered)
            
            # Compute metrics
            freqs, psd = welch(filtered, fs=fs, nperseg=fs, noverlap=fs//2)
            
            # Alpha analysis
            alpha_mask = (freqs >= 8) & (freqs <= 13)
            alpha_power = np.trapz(psd[alpha_mask], freqs[alpha_mask])
            total_power = np.trapz(psd, freqs)
            
            results[ch] = {
                'dominant_freq': freqs[np.argmax(psd)],
                'alpha_ratio': alpha_power / total_power,
                'total_power': total_power,
                'filtered_signal': filtered
            }
        
        # Identify strong alpha channels
        strong_alpha = [ch for ch, metrics in results.items() 
                       if metrics['alpha_ratio'] > 0.2]
        
        print(f"Channels with strong alpha: {strong_alpha}")
        return results
        
    except Exception as e:
        print(f"Processing error: {e}")
        return None
