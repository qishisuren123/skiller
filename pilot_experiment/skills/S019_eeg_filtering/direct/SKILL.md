# EEG Signal Filtering and Analysis

## Overview
This skill enables filtering and analysis of multi-channel EEG signals, including bandpass/notch filtering, power spectral density computation, and alpha wave detection for neurophysiological data processing.

## Workflow
1. Parse command-line arguments for input CSV, output directory, and sampling rate
2. Load EEG data from CSV and validate 8-channel format with time column
3. Apply Butterworth bandpass filter (0.5-40 Hz) and notch filter (50 Hz) to each channel
4. Compute power spectral density using Welch's method with appropriate windowing
5. Calculate alpha band power ratio (8-13 Hz) and identify dominant frequencies
6. Generate filtered signals CSV, PSD CSV, and summary JSON with statistical metrics
7. Display analysis results including channels with strong alpha activity (>0.2 ratio)

## Common Pitfalls
- **Nyquist frequency violation**: Ensure filter cutoff frequencies are below fs/2 (128 Hz for 256 Hz sampling) - use scipy.signal.butter with proper frequency normalization
- **Filter instability**: Use scipy.signal.filtfilt for zero-phase filtering instead of lfilter to avoid phase distortion and ensure stable filtering
- **PSD frequency resolution**: Choose appropriate nperseg parameter in welch() - typically fs (256 samples) for 1 Hz resolution, but adjust based on signal length
- **Alpha band integration**: Use numpy.trapz or scipy.integrate.trapz for proper power integration over frequency bands, not simple summation
- **Missing data handling**: Check for NaN values in EEG channels before filtering - use pandas.dropna() or interpolation methods

## Error Handling
- Validate CSV structure and channel count before processing
- Check sampling rate compatibility with filter parameters
- Handle file I/O errors with informative messages
- Verify sufficient data length for reliable PSD estimation (minimum 2-3 seconds)
- Catch scipy.signal filter design errors for invalid parameters

## Quick Reference
