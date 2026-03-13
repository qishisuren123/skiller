Write a Python CLI script to filter and analyze multi-channel EEG (electroencephalogram) signals.

Input: A CSV file with columns: time (seconds), ch1, ch2, ..., ch8 (8 EEG channels in microvolts).
The sampling rate is 256 Hz.

Requirements:
1. Use argparse: --input CSV path, --output directory, --sample-rate (default 256)
2. Apply a bandpass filter (0.5–40 Hz) to each channel using scipy.signal (e.g., Butterworth filter, order 4)
3. Apply a notch filter at 50 Hz (powerline interference removal) using scipy.signal
4. Compute the power spectral density (PSD) for each channel using Welch's method (scipy.signal.welch)
5. Detect alpha waves (8–13 Hz): for each channel, compute the ratio of alpha-band power to total power
6. Output files:
   - filtered_signals.csv: time column + filtered ch1–ch8
   - psd.csv: frequency column + PSD values for each channel
   - summary.json: for each channel: {dominant_frequency_Hz, alpha_power_ratio, total_power, mean_amplitude, std_amplitude}
7. Print: dominant frequency per channel, channels with strong alpha activity (ratio > 0.2)
