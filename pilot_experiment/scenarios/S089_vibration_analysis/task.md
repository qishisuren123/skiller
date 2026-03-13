# Vibration Spectrum Analysis for Fault Detection

Create a CLI tool that analyzes machine vibration data to detect potential faults by examining frequency domain characteristics and harmonic patterns.

Your script should accept vibration time series data parameters and perform spectral analysis to identify anomalous frequency components that may indicate mechanical faults such as bearing defects, misalignment, or imbalance.

## Requirements

1. **Data Generation**: Generate synthetic vibration signals with configurable sampling rate, duration, and noise level. Include a fundamental rotation frequency and its harmonics, plus optional fault frequencies.

2. **Spectral Analysis**: Compute the power spectral density (PSD) using Welch's method with appropriate windowing. Apply frequency binning and smoothing to reduce noise in the spectrum.

3. **Peak Detection**: Identify significant spectral peaks above a threshold (e.g., 3 standard deviations above mean). Extract peak frequencies, amplitudes, and quality factors.

4. **Harmonic Analysis**: Detect harmonic relationships between peaks. Identify the fundamental frequency and classify peaks as harmonics, subharmonics, or sidebands within a specified tolerance.

5. **Fault Detection**: Flag potential faults based on spectral signatures:
   - High-frequency content indicating bearing issues
   - Non-harmonic peaks suggesting looseness or misalignment
   - Amplitude ratios between harmonics outside normal ranges

6. **Output Generation**: Save results as JSON containing detected peaks, harmonic analysis, fault indicators, and diagnostic summary. Optionally save the computed spectrum as CSV.

## Command Line Interface
