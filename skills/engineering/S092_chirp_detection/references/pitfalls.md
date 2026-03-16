# Common Pitfalls in Chirp Detection

## Pickle Loading Error
**Error**: ValueError: Object arrays cannot be loaded when allow_pickle=False
**Root Cause**: .npy file contains object arrays or was saved with pickle=True, but numpy.load() defaults to allow_pickle=False for security
**Fix**: Implement fallback loading with allow_pickle=True and handle different data container types (arrays, scalar objects)

## NaN Value Propagation
**Error**: RuntimeWarning: invalid value encountered in true_divide, followed by ValueError: Input contains NaN, infinity or a value too large for dtype('float64')
**Root Cause**: NaN values in spectrogram propagate through normalization and cause sklearn regression to fail
**Fix**: Replace NaN/infinite values with minimum finite value before processing and add finite value checks throughout pipeline

## Low Confidence Scores
**Error**: All candidates have very low confidence scores (0.01-0.03) despite good R-squared values (0.8-0.9)
**Root Cause**: Confidence calculation divides signal strength by full spectrogram standard deviation, which is large for dB-scale data (10-20 dB)
**Fix**: Use SNR-based weighting by subtracting background level and normalizing to 0-1 range instead of dividing by standard deviation

## Zero Standard Deviation
**Error**: RuntimeWarning: invalid value encountered in true_divide during normalization
**Root Cause**: Constant-value spectrograms or regions have zero standard deviation causing division by zero
**Fix**: Check for zero/invalid standard deviation and skip normalization, using raw values instead
