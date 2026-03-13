# Example 1: Basic mel filterbank creation and MFCC computation
import numpy as np
from scipy.fft import dct

# Create sample power spectrum
frame_size = 1024
sample_rate = 16000
power_spectrum = np.random.rand(10, frame_size // 2 + 1)  # 10 frames

# Create mel filterbank
def create_mel_filterbank(n_filters, fft_size, sample_rate):
    mel_low, mel_high = 0, 2595 * np.log10(1 + sample_rate / 2 / 700)
    mel_points = np.linspace(mel_low, mel_high, n_filters + 2)
    hz_points = 700 * (10**(mel_points / 2595) - 1)
    bin_points = np.floor((fft_size + 1) * hz_points / sample_rate).astype(int)
    
    filterbank = np.zeros((n_filters, fft_size // 2 + 1))
    for i in range(n_filters):
        left, center, right = bin_points[i:i+3]
        if center > left:
            filterbank[i, left:center] = np.linspace(0, 1, center - left)
        if right > center:
            filterbank[i, center:right] = np.linspace(1, 0, right - center)
    return filterbank

mel_filterbank = create_mel_filterbank(26, frame_size, sample_rate)
mel_spectrum = np.dot(power_spectrum, mel_filterbank.T)
log_mel = np.log(mel_spectrum + 1e-10)
mfcc = dct(log_mel, type=2, axis=1, norm='ortho')[:, :13]

# Example 2: Complete feature extraction pipeline
def extract_all_features(signal, frame_size=1024, hop_size=512, sample_rate=16000):
    # Extract frames
    n_frames = (len(signal) - frame_size) // hop_size + 1
    frames = np.array([signal[i*hop_size:i*hop_size + frame_size] 
                      for i in range(n_frames)])
    
    # Apply window and compute STFT
    window = np.hamming(frame_size)
    windowed = frames * window
    fft_frames = np.fft.fft(windowed, axis=1)
    magnitude = np.abs(fft_frames[:, :frame_size//2 + 1])
    
    # Compute features
    zcr = np.sum(np.diff(np.sign(frames), axis=1) != 0, axis=1) / (2 * frame_size)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    
    # MFCC computation
    mel_filterbank = create_mel_filterbank(26, frame_size, sample_rate)
    power_spec = magnitude ** 2
    mel_spec = np.dot(power_spec, mel_filterbank.T)
    mfcc = dct(np.log(mel_spec + 1e-10), type=2, axis=1, norm='ortho')[:, :13]
    
    return {
        'zcr': zcr,
        'rms_energy': rms,
        'mfcc': mfcc,
        'magnitude_spectrogram': magnitude
    }

# Usage example
sample_signal = np.random.randn(16000)  # 1 second at 16kHz
features = extract_all_features(sample_signal)
print(f"Extracted {len(features['zcr'])} frames")
print(f"MFCC shape: {features['mfcc'].shape}")
