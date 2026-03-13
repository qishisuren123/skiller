# Chirp Signal Detection in Spectrograms

Create a CLI script that detects chirp signals (frequency-sweeping signals) in noisy time-frequency spectrograms. Chirp signals are characterized by their linear frequency modulation over time and are commonly found in radar, sonar, and communication systems.

Your script should accept spectrogram data as input and identify regions containing chirp signals based on their distinctive time-frequency characteristics.

## Requirements

1. **Input Processing**: Accept a NumPy array file (.npy) containing a 2D spectrogram (frequency × time) via `--input` argument. The spectrogram represents power spectral density values.

2. **Chirp Detection**: Implement a simple chirp detection algorithm that identifies linear frequency sweeps. Use a sliding window approach to detect regions where frequency content changes linearly over time.

3. **Threshold Filtering**: Accept a `--threshold` parameter (float, default=0.5) to filter out weak chirp candidates. Only report chirps with detection confidence above this threshold.

4. **Output Generation**: Save detection results to a JSON file specified by `--output` argument. Include for each detected chirp: start_time, end_time, start_frequency, end_frequency, and confidence score.

5. **Visualization**: Generate a plot showing the original spectrogram with detected chirps overlaid as colored rectangles. Save as PNG file with suffix "_detected.png" added to the output filename stem.

6. **Statistics**: Print to stdout the total number of chirps detected and the average confidence score of all detections.

## Usage Example
