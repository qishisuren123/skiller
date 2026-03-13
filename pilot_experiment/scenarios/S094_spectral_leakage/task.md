# Spectral Leakage Analysis and Correction Tool

Create a CLI tool that analyzes spectral leakage effects in frequency domain analysis and applies windowing functions to minimize artifacts. The tool should generate synthetic signals, apply various windowing techniques, and quantify the improvement in spectral quality.

## Requirements

1. **Signal Generation**: Generate a composite test signal containing multiple sinusoidal components with known frequencies, amplitudes, and phases. Add configurable white noise to simulate realistic measurement conditions.

2. **Windowing Analysis**: Implement and compare at least 4 different windowing functions (rectangular, Hann, Hamming, Blackman, and Kaiser with configurable beta parameter). Calculate the window's main lobe width and side lobe suppression characteristics.

3. **Spectral Leakage Quantification**: Compute power spectral density using FFT for both windowed and unwindowed signals. Quantify spectral leakage by measuring the power spread around true frequency components and calculate the spectral leakage ratio (power in side lobes vs main lobe).

4. **Frequency Resolution vs Leakage Trade-off**: Analyze the trade-off between frequency resolution and spectral leakage suppression for different window functions. Calculate effective noise bandwidth and processing gain for each window.

5. **Scalloping Loss Analysis**: Evaluate scalloping loss effects by computing the FFT response at frequencies between bin centers. Generate a scalloping loss curve showing amplitude variation across the frequency bin.

6. **Output Generation**: Save results as HDF5 files containing original/windowed signals, FFT results, window characteristics, and leakage metrics. Generate JSON summary with quantitative comparisons and recommendations for optimal windowing based on application requirements.

Use argparse to handle command-line arguments for signal parameters (frequencies, amplitudes, noise level), analysis parameters (FFT size, overlap), and output file paths.
