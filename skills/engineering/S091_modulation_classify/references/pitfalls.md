## Data Format Assumption Error

**Error**: IndexError: too many indices for array: array is 1-dimensional

**Root Cause**: Code assumed IQ data was in 2D [I,Q] format but user's data was already complex-valued 1D arrays

**Fix**: Added proper data format detection using np.iscomplexobj() and handling for complex128/complex64 arrays, 2D [I,Q] format, and interleaved 1D real arrays

## Clustering Sample Size Error  

**Error**: ValueError: n_clusters=8 must be <= n_samples=7

**Root Cause**: EVM calculation used fixed number of clusters (8) regardless of available samples after subsampling, causing failure when signals had very few samples

**Fix**: Implemented dynamic cluster count calculation based on sample size (max_clusters = min(8, len(samples) // 3)) with minimum threshold checks and graceful fallback to amplitude standard deviation when clustering fails
