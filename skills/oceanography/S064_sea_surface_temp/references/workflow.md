1. Set up command-line arguments including input file, output paths, and logging options
2. Configure logging system with specified level and optional file output
3. Load SST data from .npy file or generate synthetic data with realistic patterns
4. Check data quality including NaN count and uniform field detection
5. Compute climatological mean using NaN-aware numpy functions
6. Calculate temperature anomalies by subtracting climatology from original data
7. Analyze anomalies with comprehensive statistics including extremes and thresholds
8. Handle edge cases like uniform fields and missing data gracefully
9. Save results to JSON format with optional CSV grid output
10. Log all processing steps and performance metrics for debugging
