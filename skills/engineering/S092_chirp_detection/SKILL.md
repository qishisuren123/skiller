---
name: chirp_detection
description: "# Chirp Signal Detection in Spectrograms

Create a CLI script that detects chirp signals (frequency-sweeping signals) in noisy time-frequency spectrograms. Chirp signals are characterized by their linear frequency progression over time and are common in radar, sonar, and communication systems."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: engineering
---

# Chirp Detection

## Overview
This skill implements automated detection of chirp signals in 2D spectrograms using sliding window analysis and linear regression. Chirp signals are characterized by linear frequency sweeps over time and appear as diagonal lines in time-frequency representations. The algorithm handles real-world radar data challenges including NaN values, varying signal strengths, and dB-scale measurements.

## When to Use
- Detecting frequency-modulated continuous wave (FMCW) radar signals
- Analyzing sonar chirp returns in underwater acoustics
- Processing communication system sweep signals
- Quality control of chirp waveform generators
- Automated signal classification in spectrum monitoring

## Inputs
- **spectrogram**: 2D numpy array (.npy file) with shape (frequency_bins, time_bins)
- **threshold**: Detection confidence threshold (0.0-1.0, default 0.5)
- **window_size**: Sliding window size in time bins (default 10)

Data format should be power spectral density, typically in dB scale. NaN/infinite values are automatically handled.

## Workflow
1. Load spectrogram using scripts/main.py with robust error handling for pickle/object arrays
2. Clean data by replacing NaN/infinite values with minimum finite value
3. Apply sliding window across time dimension with 50% overlap
4. For each window, find peak frequency at each time step using argmax
5. Fit linear regression to frequency trajectory using sklearn
6. Calculate confidence score combining R-squared linearity with SNR-based signal strength
7. Filter detections above threshold and save results as JSON
8. Generate visualization with detected chirps overlaid as red rectangles
9. Reference references/pitfalls.md for common error patterns and solutions

## Error Handling
The system includes comprehensive error handling for common data issues:
- **Pickle errors**: Automatically retry loading with allow_pickle=True when standard loading fails
- **NaN values**: Replace non-finite values with minimum finite value and log replacement count
- **Zero variance**: Handle constant-value spectrograms by skipping normalization
- **Insufficient data**: Skip windows with <50% valid data points
- **Regression failures**: Validate finite inputs to sklearn and handle edge cases

## Common Pitfalls
- **Low confidence scores**: dB-scale data requires SNR-based weighting instead of raw standard deviation scaling
- **Object array loading**: .npy files saved with complex data structures need pickle=True parameter
- **Window size selection**: Too small windows miss long chirps, too large windows reduce time resolution
- **Threshold tuning**: Start with 0.1-0.3 for noisy radar data, 0.5+ for clean synthetic signals
- **Background estimation**: Use percentile-based background (25th) rather than mean for robust SNR calculation

## Output Format
JSON file containing detected chirps:
