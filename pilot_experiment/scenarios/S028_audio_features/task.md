Write a Python CLI script to extract audio features from synthetic audio signals stored as numpy arrays.

Input: A .npz file containing:
- signals: 2D array (n_signals x n_samples), each row is an audio waveform
- sample_rate: scalar, the sample rate in Hz
- labels: 1D string array, labels for each signal

Requirements:
1. Use argparse: --input NPZ path, --output directory, --frame-size (default 1024), --hop-size (default 512)
2. For each signal, compute frame-level features:
   a. Short-Time Fourier Transform (STFT) magnitude spectrogram
   b. Mel-Frequency Cepstral Coefficients (MFCCs): apply mel filterbank (at least 26 filters) to power spectrum, take log, then DCT to get 13 coefficients per frame. Implement mel filterbank manually using numpy (triangular filters spaced on mel scale). Use scipy.fft.dct for the DCT step.
   c. Zero-Crossing Rate (ZCR) per frame
   d. RMS energy per frame
3. Output: features.csv (columns: signal_id, frame_idx, zcr, rms_energy, mfcc_0 ... mfcc_12), summary.json (per signal: mean and std of each feature, total_frames, label)
4. Print summary: number of signals processed, total frames extracted
