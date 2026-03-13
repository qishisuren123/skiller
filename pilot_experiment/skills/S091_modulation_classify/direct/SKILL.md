# Digital Modulation Classification from IQ Samples

## Overview
This skill enables classification of digital modulation schemes (BPSK, QPSK, 8PSK, 16QAM, 64QAM) from complex-valued IQ sample data using signal processing feature extraction and machine learning classification techniques.

## Workflow
1. **Load and preprocess IQ data**: Read HDF5 files containing complex IQ samples, apply DC removal, normalization, and automatic gain control
2. **Extract signal features**: Compute instantaneous amplitude/phase statistics, constellation metrics, spectral features, higher-order moments, and zero-crossing rates
3. **Generate constellation diagrams**: Create scatter plots of normalized IQ samples and save visualization for each signal
4. **Train classification model**: Use extracted features to train a machine learning classifier with cross-validation
5. **Classify modulation schemes**: Apply trained model to predict modulation types with confidence scores
6. **Calculate performance metrics**: Generate confusion matrix, accuracy, precision/recall, and identify low-confidence predictions
7. **Export results**: Save classifications, features, and metrics to specified output files

## Common Pitfalls
- **Phase ambiguity in PSK signals**: PSK constellations can appear rotated due to carrier phase offset. Solution: Use phase-invariant features like amplitude variance ratios and differential phase statistics
- **Power normalization inconsistency**: Different signals may have vastly different power levels. Solution: Apply consistent AGC normalization based on signal variance before feature extraction
- **Frequency offset corruption**: Carrier frequency offset causes constellation rotation over time. Solution: Estimate and compensate frequency offset using FFT peak detection or apply frequency-invariant features
- **Insufficient symbol sampling**: Too few samples per symbol leads to poor constellation formation. Solution: Ensure minimum 1000 samples per signal and validate symbol rate assumptions
- **Noise floor confusion**: Very low SNR signals may be misclassified due to noise dominance. Solution: Implement SNR estimation and flag signals below threshold (-10 dB) as unreliable

## Error Handling
- Validate HDF5 file structure and complex data types before processing
- Handle missing or corrupted signal datasets gracefully with warning messages
- Implement bounds checking for feature extraction to avoid division by zero or infinite values
- Use try-catch blocks around constellation plotting to handle degenerate cases
- Validate classifier training data has sufficient samples per class (minimum 10 samples)

## Quick Reference
