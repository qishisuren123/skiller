1. Load CSV data file using pandas with automatic encoding detection
2. Execute column detection algorithm from references/pitfalls.md to identify time and elevation columns
3. Standardize column names and convert timestamps to datetime objects
4. Perform quality control checks for unrealistic values (>20m) and data gaps
5. Preprocess elevation data with linear detrending and calculate sampling frequency
6. Compute power spectral density using scipy.signal.welch with Hanning windows
7. Filter spectrum to wave frequency band (0.05-0.5 Hz) for parameter calculations
8. Calculate wave parameters including significant wave height using spectral moments
9. Validate energy conservation between wave band and total spectrum
10. Generate log-log visualization with peak frequency markers and wave band shading
11. Save results in JSON summary format and CSV spectrum data format
12. Output publication-quality PNG plot with parameter annotations
