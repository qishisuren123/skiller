import argparse
import numpy as np
import json
import csv
import os
from scipy.fft import dct, fft

def parse_arguments():
    parser = argparse.ArgumentParser(description='Extract audio features from synthetic audio signals')
    parser.add_argument('--input', required=True, help='Path to input .npz file')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--frame-size', type=int, default=1024, help='Frame size (default: 1024)')
    parser.add_argument('--hop-size', type=int, default=512, help='Hop size (default: 512)')
    return parser.parse_args()

def load_data(input_path):
    """Load signals, sample rate, and labels from npz file"""
    data = np.load(input_path)
    return data['signals'], data['sample_rate'], data['labels']

def get_n_frames(signal_length, frame_size, hop_size):
    """Calculate number of frames consistently"""
    return (signal_length - frame_size) // hop_size + 1

def hz_to_mel(hz):
    """Convert frequency in Hz to mel scale"""
    return 2595 * np.log10(1 + hz / 700)

def mel_to_hz(mel):
    """Convert mel scale to frequency in Hz"""
    return 700 * (10**(mel / 2595) - 1)

def create_mel_filterbank(n_filters, fft_size, sample_rate, low_freq=0, high_freq=None):
    """Create mel filterbank with triangular filters"""
    if high_freq is None:
        high_freq = sample_rate / 2
    
    low_mel = hz_to_mel(low_freq)
    high_mel = hz_to_mel(high_freq)
    
    mel_points = np.linspace(low_mel, high_mel, n_filters + 2)
    hz_points = mel_to_hz(mel_points)
    
    bin_points = np.floor((fft_size + 1) * hz_points / sample_rate).astype(int)
    
    filterbank = np.zeros((n_filters, fft_size // 2 + 1))
    
    for i in range(n_filters):
        left = bin_points[i]
        center = bin_points[i + 1]
        right = bin_points[i + 2]
        
        for j in range(left, center):
            filterbank[i, j] = (j - left) / (center - left)
        
        for j in range(center, right):
            filterbank[i, j] = (right - j) / (right - center)
    
    return filterbank

def compute_stft(sig, frame_size, hop_size):
    """Compute STFT magnitude spectrogram manually"""
    window = np.hanning(frame_size)
    n_frames = get_n_frames(len(sig), frame_size, hop_size)
    spectrogram = np.zeros((frame_size // 2 + 1, n_frames))
    
    for i in range(n_frames):
        start = i * hop_size
        end = start + frame_size
        if end > len(sig):
            frame = np.zeros(frame_size)
            frame[:len(sig)-start] = sig[start:]
        else:
            frame = sig[start:end]
        
        frame = frame * window
        fft_frame = fft(frame)[:frame_size // 2 + 1]
        spectrogram[:, i] = np.abs(fft_frame)
    
    return spectrogram

def compute_zcr(sig, frame_size, hop_size):
    """Compute Zero Crossing Rate per frame"""
    n_frames = get_n_frames(len(sig), frame_size, hop_size)
    zcr = np.zeros(n_frames)
    
    for i in range(n_frames):
        start = i * hop_size
        end = start + frame_size
        if end > len(sig):
            frame = np.zeros(frame_size)
            frame[:len(sig)-start] = sig[start:]
        else:
            frame = sig[start:end]
        
        zero_crossings = np.sum(np.abs(np.diff(np.sign(frame)))) / 2
        zcr[i] = zero_crossings / frame_size
    
    return zcr

def compute_rms_energy(sig, frame_size, hop_size):
    """Compute RMS energy per frame"""
    n_frames = get_n_frames(len(sig), frame_size, hop_size)
    rms = np.zeros(n_frames)
    
    for i in range(n_frames):
        start = i * hop_size
        end = start + frame_size
        if end > len(sig):
            frame = np.zeros(frame_size)
            frame[:len(sig)-start] = sig[start:]
        else:
            frame = sig[start:end]
        
        rms[i] = np.sqrt(np.mean(frame ** 2))
    
    return rms

def compute_mfcc(spectrogram, sample_rate, n_mfcc=13, n_filters=26):
    """Compute MFCC features"""
    filterbank = create_mel_filterbank(n_filters, (spectrogram.shape[0]-1)*2, sample_rate)
    power_spec = spectrogram ** 2
    mel_spec = np.dot(filterbank, power_spec)
    log_mel_spec = np.log(mel_spec + 1e-10)
    
    mfcc = dct(log_mel_spec, axis=0, norm='ortho')
    return mfcc[:n_mfcc].T

def main():
    args = parse_arguments()
    
    os.makedirs(args.output, exist_ok=True)
    
    signals, sample_rate, labels = load_data(args.input)
    
    print(f"Loaded {len(signals)} signals with sample rate {sample_rate} Hz")
    print(f"Frame size: {args.frame_size}, Hop size: {args.hop_size}")
    
    csv_path = os.path.join(args.output, 'features.csv')
    json_path = os.path.join(args.output, 'summary.json')
    
    csv_header = ['signal_id', 'frame_idx', 'zcr', 'rms_energy'] + [f'mfcc_{i}' for i in range(13)]
    
    all_features = []
    summary_data = {}
    total_frames = 0
    
    for signal_id, (sig, label) in enumerate(zip(signals, labels)):
        print(f"Processing signal {signal_id + 1}/{len(signals)}")
        
        spectrogram = compute_stft(sig, args.frame_size, args.hop_size)
        mfcc_features = compute_mfcc(spectrogram, sample_rate)
        zcr_features = compute_zcr(sig, args.frame_size, args.hop_size)
        rms_features = compute_rms_energy(sig, args.frame_size, args.hop_size)
        
        n_frames = len(zcr_features)
        total_frames += n_frames
        
        for frame_idx in range(n_frames):
            row = [signal_id, frame_idx, zcr_features[frame_idx], rms_features[frame_idx]]
            row.extend(mfcc_features[frame_idx])
            all_features.append(row)
        
        summary_data[f'signal_{signal_id}'] = {
            'label': label,
            'total_frames': n_frames,
            'zcr_mean': float(np.mean(zcr_features)),
            'zcr_std': float(np.std(zcr_features)),
            'rms_energy_mean': float(np.mean(rms_features)),
            'rms_energy_std': float(np.std(rms_features))
        }
        
        for i in range(13):
            summary_data[f'signal_{signal_id}'][f'mfcc_{i}_mean'] = float(np.mean(mfcc_features[:, i]))
            summary_data[f'signal_{signal_id}'][f'mfcc_{i}_std'] = float(np.std(mfcc_features[:, i]))
    
    with open(csv_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_header)
        writer.writerows(all_features)
    
    with open(json_path, 'w') as jsonfile:
        json.dump(summary_data, jsonfile, indent=2)
    
    print(f"\nSummary:")
    print(f"Number of signals processed: {len(signals)}")
    print(f"Total frames extracted: {total_frames}")
    print(f"Features saved to: {csv_path}")
    print(f"Summary saved to: {json_path}")

if __name__ == "__main__":
    main()
