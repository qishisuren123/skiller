# Adaptive Echo Cancellation for Audio Signals

## Overview
This skill implements adaptive echo cancellation using autocorrelation analysis and digital signal processing techniques to remove delayed echo artifacts from synthetic audio recordings, with quality assessment and visualization capabilities.

## Workflow
1. **Load and validate audio data** - Read .npy file containing normalized 1D audio signal and verify format
2. **Perform autocorrelation analysis** - Calculate normalized autocorrelation to identify echo delay and attenuation characteristics
3. **Detect echo parameters** - Find secondary peaks in autocorrelation to determine delay (samples) and attenuation factor
4. **Apply adaptive echo cancellation** - Subtract delayed and attenuated signal copy using detected parameters
5. **Calculate quality metrics** - Compute ERLE and Signal-to-Echo Ratio improvement to assess cancellation effectiveness
6. **Generate outputs** - Save processed signal as .npy file and create JSON report with metrics
7. **Create visualization** - Plot time-domain comparison and autocorrelation functions for analysis

## Common Pitfalls
- **Autocorrelation window too short**: Use at least 2x expected maximum delay to capture echo peaks properly
- **False peak detection**: Filter autocorrelation results and use minimum peak prominence to avoid noise artifacts
- **Over-cancellation artifacts**: Limit attenuation factor estimation to realistic range (0.2-0.7) to prevent signal distortion
- **Edge effects in filtering**: Apply proper windowing and handle signal boundaries when subtracting delayed copies
- **Normalization issues**: Maintain signal amplitude range [-1, 1] throughout processing to prevent clipping

## Error Handling
- Validate input signal format and range before processing
- Handle cases where no significant echo is detected (return original signal)
- Implement bounds checking for delay and attenuation parameters
- Use try-catch blocks for file I/O operations with informative error messages

## Quick Reference
