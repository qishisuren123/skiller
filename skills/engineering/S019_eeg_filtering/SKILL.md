---
name: eeg_filtering
description: "Write a Python CLI script to filter and analyze multi-channel EEG (electroencephalogram) signals.

Input: A CSV file with columns: time (seconds), ch1, ch2, ..., ch8 (8 EEG channels in microvolts).
Output: Filtered signals, power spectral density analysis, and alpha wave detection with memory-efficient processing for large datasets."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: engineering
---

# EEG Filtering

## Overview
This skill provides a complete Python CLI tool for processing multi-channel EEG signals. It applies bandpass filtering (0.5-40 Hz), removes powerline interference (50 Hz notch filter), computes power spectral density using Welch's method, and detects alpha wave activity (8-13 Hz). The tool is optimized for large datasets using chunked processing to handle memory constraints efficiently.

## When to Use
- Processing raw EEG recordings from multi-channel systems
- Analyzing alpha wave activity in occipital channels
- Cleaning EEG signals with NaN values or artifacts
- Working with large datasets (hours of recordings) that exceed memory limits
- Generating standardized EEG analysis reports with PSD and frequency analysis

## Inputs
- CSV file with columns: time, ch1, ch2, ..., ch8 (8 EEG channels)
- Sample rate (default: 256 Hz)
- Output directory path

## Workflow
1. Execute `scripts/main.py` with input CSV and output directory
2. Script loads data in chunks to manage memory usage
3. Applies signal cleaning to handle NaN values and outliers
4. Processes each channel with bandpass and notch filters
5. Computes PSD analysis on downsampled data for efficiency
6. Generates filtered signals, PSD data, and summary statistics
7. Refer to `references/workflow.md` for detailed processing steps
8. Check `references/pitfalls.md` for common error handling patterns

## Error Handling
The script includes comprehensive error handling for common EEG processing issues. It can handle and recover from NaN values in signals, memory constraints with large datasets, inconsistent PSD array lengths, and file I/O operations. The chunked processing approach prevents memory overflow errors while maintaining analysis accuracy.

## Common Pitfalls
- File I/O errors during CSV writing operations
- NaN values causing filter instability and divide warnings
- Memory overflow with large datasets when loading entire files
- PSD array length mismatches between channels
- Data type conversion errors in NumPy operations

## Output Format
- `filtered_signals.csv`: Time series data with filtered EEG channels
- `psd.csv`: Power spectral density data with frequency bins
- `summary.json`: Channel statistics including dominant frequencies and alpha ratios
