# Adaptive Noise Cancellation for Audio Signals

Create a CLI script that implements adaptive noise cancellation on synthetic audio signals using the Least Mean Squares (LMS) algorithm. The script should process noisy signals and produce cleaned outputs with performance metrics.

Your script should accept the following arguments:
- `--input-signal`: Path to save the generated noisy input signal (NumPy array file)
- `--output-signal`: Path to save the cleaned signal after noise cancellation
- `--reference-noise`: Path to save the reference noise signal used for adaptation
- `--step-size`: Learning rate for the LMS algorithm (default: 0.01)
- `--filter-length`: Number of taps in the adaptive filter (default: 32)
- `--metrics-file`: Path to save performance metrics as JSON

## Requirements:

1. **Signal Generation**: Generate a composite test signal containing a 440Hz sine wave, a 880Hz sine wave, and broadband noise. The signal should be 2 seconds long at 8kHz sampling rate.

2. **Reference Noise**: Create a correlated reference noise signal that shares common components with the noise in the primary signal but is delayed and scaled differently.

3. **LMS Implementation**: Implement the Least Mean Squares adaptive filter algorithm to estimate and cancel the noise component. The filter should adapt its coefficients iteratively to minimize the error between desired and actual outputs.

4. **Performance Metrics**: Calculate and save Signal-to-Noise Ratio (SNR) improvement, Mean Squared Error (MSE) reduction, and filter convergence rate. Compare metrics before and after noise cancellation.

5. **Output Files**: Save the cleaned signal, reference noise, and original noisy signal as NumPy arrays. Ensure all signals maintain the same sampling rate and duration.

6. **Validation**: Implement bounds checking for step size (0.001 to 0.1) and filter length (8 to 128 taps) to ensure algorithm stability.

The script should demonstrate effective noise reduction while preserving the original signal components, with quantifiable improvements in signal quality metrics.
