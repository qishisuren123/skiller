import argparse
import numpy as np
import pandas as pd
import json
import os
from scipy.fft import fft, dct

def hz_to_mel(hz):
    """Convert frequency in Hz to mel scale"""
    return 2595 * np.log10(1 + hz / 700)

def mel_to_hz(mel):
    """Convert mel scale to frequency in Hz"""
    return 700 * (10**(mel / 2595) - 1)

def create_mel_filterbank(n_filters, fft_size, sample_rate):
    """Create mel filterbank with triangular filters"""
    mel_low, mel_high = 0, hz_to_mel(sample_rate / 2)
    mel_points = np.linspace(mel_low, mel_high, n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    bin_points = np.floor((fft_size + 1) * hz_points / sample_rate).astype(int)
    
    filterbank = np.zeros((n_filters, fft_size // 2 + 1))
    for i in range(n_filters):
        left, center, right = bin_points[i:i+3]
        if center > left:
            filterbank[i, left:center] = np.linspace(0, 1, center - left)
        if right > center:
            filterbank[i, center:right] = np.linspace(1, 0, right - center)
    return filterbank

def extract_frames(signal, frame_size, hop_size):
    """Extract overlapping frames from signal"""
    n_frames = (len(signal) - frame_size) // hop_size + 1
    frames = np.zeros((n_frames, frame_size))
    for i in range(n_frames):
        start = i * hop_size
        frames[i] = signal[start:start + frame_size]
    return frames

def compute_stft_magnitude(frames):
    """Compute STFT magnitude spectrogram"""
    # Apply Hamming window
    window = np.hamming(frames.shape[1])
    windowed_frames = frames * window
    
    # Compute FFT and magnitude
    fft_frames = fft(windowed_frames, axis=1)
    magnitude = np.abs(fft_frames[:, :frames.shape[1]//2 + 1])
    return magnitude

def compute_mfcc(magnitude_spectrogram, mel_filterbank, n_mfcc=13):
    """Compute MFCC features"""
    # Apply mel filterbank to power spectrum
    power_spectrum = magnitude_spectrogram ** 2
    mel_spectrum = np.dot(power_spectrum, mel_filterbank.T)
    
    # Take log (add small epsilon to avoid log(0))
    log_mel_spectrum = np.log(mel_spectrum + 1e-10)
    
    # Apply DCT to get MFCC coefficients
    mfcc = dct(log_mel_spectrum, type=2, axis=1, norm='ortho')[:, :n_mfcc]
    return mfcc

def compute_zcr(frames):
    """Compute Zero Crossing Rate for each frame"""
    # Sign changes indicate zero crossings
    sign_changes = np.diff(np.sign(frames), axis=1)
    zcr = np.sum(sign_changes != 0, axis=1) / (2 * frames.shape[1])
    return zcr

def compute_rms_energy(frames):
    """Compute RMS energy for each frame"""
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    return rms

def main():
    parser = argparse.ArgumentParser(description='Extract audio features from synthetic signals')
    parser.add_argument('--input', required=True, help='Input NPZ file path')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--frame-size', type=int, default=1024, help='Frame size in samples')
    parser.add_argument('--hop-size', type=int, default=512, help='Hop size in samples')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.frame_size <= 0 or args.hop_size <= 0:
        raise ValueError("Frame size and hop size must be positive")
    if args.hop_size >= args.frame_size:
        raise ValueError("Hop size should be smaller than frame size")
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    try:
        data = np.load(args.input)
        signals = data['signals']
        sample_rate = int(data['sample_rate'])
        labels = data['labels']
    except KeyError as e:
        raise ValueError(f"Required key {e} not found in NPZ file")
    
    # Validate data shapes
    if signals.ndim != 2:
        raise ValueError("Signals must be 2D array (n_signals x n_samples)")
    if len(labels) != signals.shape[0]:
        raise ValueError("Number of labels must match number of signals")
    
    # Create mel filterbank
    n_mel_filters = 26
    mel_filterbank = create_mel_filterbank(n_mel_filters, args.frame_size, sample_rate)
    
    # Initialize storage for results
    all_features = []
    summary_stats = {}
    total_frames = 0
    
    print(f"Processing {len(signals)} signals...")
    
    for signal_id, (signal, label) in enumerate(zip(signals, labels)):
        # Skip if signal is too short
        if len(signal) < args.frame_size:
            print(f"Warning: Signal {signal_id} too short, skipping")
            continue
            
        # Extract frames
        frames = extract_frames(signal, args.frame_size, args.hop_size)
        n_frames = len(frames)
        total_frames += n_frames
        
        # Compute features
        magnitude_spec = compute_stft_magnitude(frames)
        mfcc_features = compute_mfcc(magnitude_spec, mel_filterbank)
        zcr = compute_zcr(frames)
        rms_energy = compute_rms_energy(frames)
        
        # Store frame-level features
        for frame_idx in range(n_frames):
            feature_row = {
                'signal_id': signal_id,
                'frame_idx': frame_idx,
                'zcr': zcr[frame_idx],
                'rms_energy': rms_energy[frame_idx]
            }
            # Add MFCC coefficients
            for i in range(mfcc_features.shape[1]):
                feature_row[f'mfcc_{i}'] = mfcc_features[frame_idx, i]
            
            all_features.append(feature_row)
        
        # Compute summary statistics
        all_frame_features = np.column_stack([zcr, rms_energy, mfcc_features])
        feature_names = ['zcr', 'rms_energy'] + [f'mfcc_{i}' for i in range(mfcc_features.shape[1])]
        
        summary_stats[f'signal_{signal_id}'] = {
            'label': str(label),
            'total_frames': n_frames,
            'feature_stats': {
                name: {
                    'mean': float(np.mean(all_frame_features[:, i])),
                    'std': float(np.std(all_frame_features[:, i]))
                }
                for i, name in enumerate(feature_names)
            }
        }
    
    # Save results
    features_df = pd.DataFrame(all_features)
    features_df.to_csv(os.path.join(args.output, 'features.csv'), index=False)
    
    with open(os.path.join(args.output, 'summary.json'), 'w') as f:
        json.dump(summary_stats, f, indent=2)
    
    print(f"Processing complete!")
    print(f"Signals processed: {len(summary_stats)}")
    print(f"Total frames extracted: {total_frames}")
    print(f"Features saved to: {os.path.join(args.output, 'features.csv')}")
    print(f"Summary saved to: {os.path.join(args.output, 'summary.json')}")

if __name__ == "__main__":
    main()
