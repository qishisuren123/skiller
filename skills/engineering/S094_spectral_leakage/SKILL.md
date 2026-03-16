---
name: spectral_leakage
description: "# Spectral Leakage Analysis and Correction Tool

Create a CLI tool that analyzes spectral leakage effects in frequency domain analysis and applies windowing functions to minimize artifacts. The tool supports multiple windowing functions and quantifies leakage ratios around true frequency components."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: engineering
---

# Spectral Leakage Analysis and Correction Tool

## Overview
This tool analyzes spectral leakage effects in frequency domain analysis by generating composite test signals and applying various windowing functions. It quantifies how power spreads around true frequency components and calculates spectral leakage ratios to help researchers understand and minimize spectral artifacts.

## When to Use
- Analyzing frequency domain artifacts in signal processing applications
- Comparing effectiveness of different windowing functions
- Quantifying spectral leakage in multi-tone signals
- Research requiring precise frequency domain analysis
- Optimizing window selection for specific signal characteristics

## Inputs
- Signal frequencies (Hz) - list of sinusoidal component frequencies
- Signal amplitudes - corresponding amplitude values
- Signal phases (optional) - phase values in radians
- Noise level - white noise standard deviation
- Sample rate and duration parameters
- FFT size and Kaiser window beta parameter

## Workflow
1. Execute `scripts/main.py` with desired signal parameters
2. Tool generates composite test signal with multiple sinusoidal components
3. Applies rectangular, Hann, Hamming, Blackman, and Kaiser windows
4. Computes power spectral density for each windowing function
5. Quantifies spectral leakage by measuring main lobe vs side lobe power
6. Analyzes window characteristics including main lobe width and side lobe suppression
7. Outputs comprehensive leakage metrics and window performance data
8. Saves results to HDF5 format as specified in `references/workflow.md`

## Error Handling
The tool includes robust error handling for common issues. Array broadcasting errors are handled by ensuring consistent data types and dimensions. Division by zero errors in logarithmic calculations are handled using maximum clamping. Empty array errors in side lobe analysis are handled by checking bounds before array slicing. The error handling ensures graceful degradation when encountering edge cases in window analysis.

## Common Pitfalls
- Mismatched array dimensions between signal and window functions
- Division by zero in window characteristic calculations
- Empty side lobe regions causing index errors
- Insufficient frequency resolution for accurate leakage quantification
- Improper normalization leading to incorrect power measurements

## Output Format
The tool outputs a structured analysis including:
- Spectral leakage ratios in dB for each frequency component
- Window characteristics (main lobe width, side lobe suppression, processing gain)
- Frequency error measurements between true and detected peaks
- Power distribution metrics (main lobe, side lobe, total power)
- Comprehensive HDF5 file with all analysis data and metadata
