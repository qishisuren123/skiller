# Audio Feature Extraction from Synthetic Signals

## Overview
This skill enables extraction of frame-level audio features (STFT, MFCCs, ZCR, RMS energy) from synthetic audio signals stored in NPZ format, with manual implementation of mel filterbank for MFCC computation.

## Workflow
1. Parse command-line arguments for input NPZ file, output directory, frame size, and hop size
2. Load audio signals, sample rate, and labels from the NPZ file
3. For each signal, apply windowing to extract overlapping frames based on frame_size and hop_size
4. Compute STFT magnitude spectrogram for each frame using numpy FFT
5. Calculate mel-frequency cepstral coefficients by implementing triangular mel filterbank, applying to power spectrum, taking log, and computing DCT
6. Extract zero-crossing rate and RMS energy for each frame
7. Save frame-level features to CSV and signal-level statistics to JSON summary

## Common Pitfalls
- **Mel scale conversion errors**: Use correct mel-to-Hz formula: `hz = 700 * (10^(mel/2595) - 1)` and inverse. Solution: Implement helper functions with proper mathematical constants.
- **Frame boundary handling**: Last frame may be shorter than frame_size. Solution: Zero-pad incomplete frames or skip them consistently.
- **STFT frequency bin mapping**: Ensure mel filterbank maps to correct frequency bins. Solution: Use `np.fft.fftfreq()` to get exact frequency values for each FFT bin.
- **DCT coefficient indexing**: MFCC features typically exclude the 0th coefficient (DC component). Solution: Take coefficients 1-13 or clarify if 0th coefficient should be included.
- **Memory efficiency**: Large signals can cause memory issues when processing all frames at once. Solution: Process signals individually and use generators for frame extraction.

## Error Handling
- Validate NPZ file contains required keys ('signals', 'sample_rate', 'labels') with appropriate shapes
- Check that frame_size and hop_size are positive integers and frame_size > hop_size
- Handle edge cases where signal length is shorter than frame_size
- Ensure output directory exists or create it, handle file write permissions
- Validate sample_rate is positive and reasonable (e.g., 8kHz - 96kHz range)

## Quick Reference
