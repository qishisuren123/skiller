# ECG QRS Complex Detection and Heart Rate Variability Analysis

Create a CLI script that detects QRS complexes in ECG signals and computes heart rate variability (HRV) metrics. The script should process synthetic ECG data and output both detection results and HRV statistics.

## Requirements

1. **Signal Processing**: Implement a QRS detection algorithm using signal filtering and peak detection. Apply a bandpass filter (5-15 Hz) to enhance QRS complexes, then use adaptive thresholding to identify R-peaks in the filtered signal.

2. **R-R Interval Calculation**: Calculate R-R intervals (time differences between consecutive R-peaks) in milliseconds. Remove physiologically implausible intervals (< 300ms or > 2000ms) as artifacts.

3. **HRV Time-Domain Metrics**: Compute standard HRV metrics including:
   - RMSSD: Root mean square of successive R-R interval differences
   - SDNN: Standard deviation of all R-R intervals
   - pNN50: Percentage of successive R-R intervals differing by > 50ms

4. **Detection Validation**: Implement quality checks for detected QRS complexes, including minimum distance constraints between peaks and signal-to-noise ratio assessment.

5. **Output Generation**: Save detected R-peak locations to a CSV file with timestamps and amplitudes. Export HRV metrics to a JSON file with computed statistics.

6. **Visualization**: Generate a plot showing the original ECG signal, filtered signal, and detected R-peaks with clear markers and labels.

## Command Line Interface
