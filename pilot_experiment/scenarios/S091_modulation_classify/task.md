# Digital Modulation Classification from IQ Samples

Create a CLI script that classifies digital modulation schemes from in-phase and quadrature (IQ) sample data. Your script should analyze complex-valued signals and identify the modulation type using signal processing and machine learning techniques.

## Requirements

1. **Data Input**: Accept IQ samples as input via `--input-file` (HDF5 format containing complex-valued time series data) and output classification results to `--output-file` (JSON format). The input file contains datasets named 'signal_X' where X is an integer, each containing complex IQ samples.

2. **Feature Extraction**: Extract at least 6 different signal features for classification including: instantaneous amplitude statistics, instantaneous phase statistics, constellation diagram features, spectral characteristics, higher-order moments, and zero-crossing rate. Save extracted features to `--features-file` as JSON.

3. **Modulation Classification**: Implement a classifier to distinguish between at least 5 modulation types: BPSK, QPSK, 8PSK, 16QAM, and 64QAM. Use extracted features to train and evaluate the classifier with cross-validation.

4. **Signal Preprocessing**: Apply appropriate preprocessing including normalization, DC removal, and optional noise reduction. Handle signals with different SNR levels and apply automatic gain control to normalize signal power.

5. **Constellation Analysis**: Generate and save constellation diagrams for each input signal to `--constellation-dir` directory. Analyze constellation clustering to aid classification and compute constellation-based metrics like error vector magnitude (EVM).

6. **Performance Metrics**: Calculate and report classification accuracy, confusion matrix, and per-class precision/recall. Include confidence scores for each prediction and identify signals that may be corrupted or contain unknown modulation types.

The script should be robust to noise and work with realistic signal impairments including frequency offset, phase noise, and timing errors commonly found in digital communication systems.
