# Audio Feature Extraction from Synthetic Signals

## Overview
This skill helps create a Python CLI script to extract audio features (MFCC, ZCR, RMS energy) from synthetic audio signals stored in .npz format, with proper frame alignment and output formatting.

## Workflow
1. **Set up argument parsing** with input file, output directory, frame size, and hop size parameters
2. **Implement consistent frame calculation** using a shared function to avoid frame count mismatches
3. **Create mel filterbank** with proper Hz-to-mel scale conversion for MFCC computation
4. **Implement STFT manually** using numpy FFT with Hanning window for compatibility
5. **Extract time-domain features** (ZCR, RMS energy) with same frame calculation
6. **Extract frequency-domain features** (MFCC) from STFT spectrogram
7. **Process all signals** in a loop with progress indication
8. **Output results** in both CSV (frame-level) and JSON (summary statistics) formats

## Common Pitfalls
- **STFT import error**: `scipy.signal.stft` not available in older scipy versions - implement manually using numpy FFT
- **Frame count mismatch**: Different frame calculations between STFT and time-domain features - use consistent `get_n_frames()` function
- **MFCC indexing error**: Applying DCT slice incorrectly - slice after DCT but before transpose
- **Edge case handling**: Signal length not divisible by hop size - pad frames with zeros when needed
- **Log of zero**: Taking log of mel spectrogram - add small epsilon (1e-10) to avoid log(0)

## Error Handling
- Check for valid input file existence and format
- Handle signals shorter than frame size by zero-padding
- Add epsilon to prevent log(0) in MFCC computation
- Create output directory if it doesn't exist
- Validate that all feature arrays have same number of frames before processing

## Quick Reference
