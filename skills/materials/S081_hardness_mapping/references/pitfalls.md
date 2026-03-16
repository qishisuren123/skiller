# Common Pitfalls and Solutions

## File Path Handling Error
**Error**: `TypeError: expected str, bytes or os.PathLike object, not method`
**Root Cause**: Passing `filepath.suffix` (a method) instead of `filepath` (the path) to pandas functions
**Fix**: Convert Path objects to strings using `str(filepath)` when passing to pandas read functions

## Kriging Performance Issues
**Error**: Kriging interpolation hangs or takes excessive time with large datasets (>500 points)
**Root Cause**: Gaussian Process regression has O(n³) complexity, becoming prohibitively slow with many training points
**Fix**: Implement subsampling using K-means clustering to select representative points, and use chunked prediction for large grids with progress indication

## Column Detection Failures
**Error**: `ValueError: Could not identify X, Y, and Hardness columns`
**Root Cause**: Non-standard column naming that doesn't match expected patterns ('x', 'y', 'hard', 'h', 'gpa')
**Fix**: Enhanced flexible column detection with case-insensitive matching and multiple keyword patterns, plus error logging showing available columns

## Memory Issues During Grid Processing
**Error**: Memory exhaustion during interpolation of high-resolution grids
**Root Cause**: Large grid arrays and distance matrices exceed available memory
**Fix**: Implement chunked processing for grid predictions with configurable chunk sizes and progress tracking using tqdm
