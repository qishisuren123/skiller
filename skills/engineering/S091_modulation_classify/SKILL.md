---
name: modulation_classify
description: "# Digital Modulation Classification from IQ Samples

Create a CLI script that classifies digital modulation schemes from in-phase and quadrature (IQ) sample data. Your script should analyze complex-valued time series data from HDF5 files and identify modulation types like BPSK, QPSK, 8PSK, 16QAM, and 64QAM using feature extraction and unsupervised clustering."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: engineering
---

# Modulation Classify

## Overview
This tool performs digital modulation classification from IQ (in-phase/quadrature) samples stored in HDF5 files. It extracts signal features, applies noise reduction preprocessing, generates constellation diagrams, and uses unsupervised machine learning to classify modulation schemes without requiring labeled training data.

## When to Use
- Analyzing unknown RF signals to identify modulation types
- Processing noisy IQ data that needs constellation analysis
- Batch processing multiple signals for modulation identification
- Research applications requiring feature extraction from complex signals
- Signal intelligence and spectrum analysis tasks

## Inputs
- HDF5 file containing complex-valued IQ samples in datasets named 'signal_*'
- IQ data can be complex128/complex64 arrays or real arrays in [I,Q] format
- Signals with various SNR levels and modulation schemes

## Workflow
1. Execute scripts/main.py with required arguments for input/output files
2. Load IQ samples from HDF5 datasets and handle format conversion
3. Apply noise reduction preprocessing using median filtering and smoothing
4. Extract comprehensive signal features including amplitude/phase statistics, EVM, and spectral characteristics
5. Generate constellation diagrams for visual analysis
6. Perform unsupervised clustering to classify modulation types
7. Calculate confidence scores and clustering quality metrics
8. Save results and features to JSON files as specified in references/workflow.md

## Error Handling
The tool includes robust error handling for common issues. When clustering fails due to insufficient samples, it gracefully falls back to alternative feature calculations. File format errors are caught and logged with descriptive messages to help users handle different IQ data formats correctly.

## Common Pitfalls
- Assuming incorrect IQ data format (2D vs 1D vs complex arrays)
- Insufficient samples for clustering algorithms causing n_clusters > n_samples errors
- Not handling edge cases with very short signals or extreme noise levels
- Missing proper data validation and NaN handling in feature extraction

## Output Format
- JSON classification results with predicted modulation, confidence scores, and cluster IDs
- JSON feature file containing extracted signal characteristics
- PNG constellation diagrams for visual verification
- Metadata including clustering quality metrics and processing parameters
