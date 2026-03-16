1. Parse command line arguments for data points and output file paths
2. Create output directories using Path.mkdir() with parents=True
3. Generate synthetic spirometry data with realistic flow patterns
4. Calculate FEV1 using optimized sampling rate-based indexing
5. Calculate FVC using vectorized operations for end-point detection
6. Validate parameters against physiological ranges
7. Create flow-volume loop plot with downsampling for large datasets
8. Save results to JSON with validation warnings and errors
9. Log all results and file locations for verification
