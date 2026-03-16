1. Prepare HDF5 input file with IQ samples in datasets named 'signal_0', 'signal_1', etc.
2. Create output directory for constellation diagrams
3. Run the main script with required arguments: --input-file, --output-file, --features-file, --constellation-dir
4. Script loads and validates IQ data format (complex arrays, [I,Q] pairs, or interleaved format)
5. Apply preprocessing including DC removal, noise reduction (median filtering, smoothing), and AGC normalization
6. Extract comprehensive signal features: amplitude/phase statistics, EVM, spectral characteristics, higher-order moments
7. Generate constellation diagrams with subsampling for large datasets
8. Perform K-means clustering on standardized features to classify modulation types
9. Calculate confidence scores based on distance to cluster centers
10. Save classification results, extracted features, and constellation plots
11. Output includes clustering quality metrics and processing metadata
