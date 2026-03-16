1. Validate input parameters (duration, sampling interval, amplitude threshold)
2. Estimate memory usage and check against system limits
3. Set random seed if provided for reproducible results
4. Generate synthetic tidal time series with M2, S2, O1 constituents
5. Add realistic Gaussian noise to synthetic data
6. Calculate frequency resolution based on data duration
7. Perform FFT on detrended tidal height data
8. Extract positive frequencies and convert to periods
9. Calculate amplitudes and phases from complex FFT results
10. Match identified periods to known tidal constituents using adaptive tolerance
11. Remove duplicate constituents and sort by amplitude
12. Save results in JSON format and optionally CSV format
13. Create time series visualization with subsampling for large datasets
14. Log comparison between true and identified constituents
