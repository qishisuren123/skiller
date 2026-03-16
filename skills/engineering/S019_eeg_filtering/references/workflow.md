1. Load EEG CSV data with time and 8 channel columns (ch1-ch8)
2. Initialize chunked processing with 50k sample chunks for memory efficiency
3. Pre-compute Butterworth bandpass (0.5-40 Hz) and notch (50 Hz) filter coefficients
4. For each chunk:
   - Clean signals by interpolating NaN values and clipping outliers
   - Apply bandpass and notch filters using pre-computed coefficients
   - Write filtered data directly to output CSV to avoid memory accumulation
   - Downsample and accumulate data for PSD computation
5. Compute power spectral density using Welch's method on accumulated data
6. Analyze alpha wave activity (8-13 Hz) relative to total EEG power (0.5-40 Hz)
7. Generate summary statistics including dominant frequencies and alpha ratios
8. Save filtered signals, PSD data, and summary JSON to output directory
