# Adaptive Noise Cancellation with LMS Algorithm

## Overview
This skill implements adaptive noise cancellation using the Least Mean Squares (LMS) algorithm to remove correlated noise from audio signals while preserving the original signal components. It generates synthetic test signals, applies adaptive filtering, and provides quantitative performance metrics.

## Workflow
1. **Parse CLI arguments** and validate step size (0.001-0.1) and filter length (8-128 taps) parameters
2. **Generate composite test signal** with 440Hz and 880Hz sine waves plus broadband noise at 8kHz sampling rate for 2 seconds
3. **Create correlated reference noise** by applying delay and scaling to noise components that correlate with primary signal noise
4. **Initialize LMS adaptive filter** with specified number of taps and zero initial coefficients
5. **Apply LMS algorithm iteratively** to estimate noise, update filter coefficients using gradient descent, and subtract estimated noise
6. **Calculate performance metrics** including SNR improvement, MSE reduction, and convergence rate analysis
7. **Save all outputs** including cleaned signal, reference noise, original signal as NumPy arrays, and metrics as JSON

## Common Pitfalls
- **Step size too large**: Causes filter instability and divergence. Solution: Validate step size is between 0.001-0.1 and use adaptive step size if needed
- **Insufficient filter length**: Results in poor noise estimation. Solution: Use at least 32 taps for broadband noise, validate range 8-128
- **Poor reference noise correlation**: Leads to ineffective cancellation. Solution: Ensure reference noise shares spectral components with primary noise but is not identical
- **Numerical overflow in coefficient updates**: Occurs with high-amplitude signals. Solution: Normalize input signals and implement coefficient bounds checking
- **Incorrect delay compensation**: Causes phase misalignment between signals. Solution: Account for processing delays in reference signal alignment

## Error Handling
- Validate all file paths are writable before processing
- Check signal lengths match between primary and reference inputs
- Implement coefficient bounds to prevent filter instability
- Handle division by zero in SNR calculations using epsilon values
- Verify sampling rate consistency across all generated signals

## Quick Reference
