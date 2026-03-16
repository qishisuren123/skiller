## PCA Convergence Error

**Error**: `numpy.linalg.LinAlgError: eigenvalues did not converge` during PCA computation

**Root Cause**: Missing values (NaN) in measurement data caused issues during standardization, leading to NaN values in covariance matrix and eigendecomposition failure

**Fix**: Added proper missing value handling by dropping incomplete records before PCA, checking for zero standard deviations, and using `np.linalg.eigh()` for symmetric matrices instead of `eig()`

## PCA DataFrame Dimension Mismatch

**Error**: `ValueError: arrays must all be the same length` when creating PCA results DataFrame

**Root Cause**: Incorrect indexing of loadings matrix - trying to assign entire rows/columns at once instead of individual elements

**Fix**: Restructured PCA DataFrame creation to build row by row, correctly extracting `loadings[variable_index, component_index]` for each component

## Infinite Values in Shape Indices

**Error**: Infinite values appearing in morphometrics.csv output due to division by zero

**Root Cause**: Zero or negative values in width/height measurements causing division by zero in elongation, flatness, and other shape index calculations

**Fix**: Added comprehensive data validation using `np.where()` conditions to check for positive values before calculations, setting invalid results to NaN instead of infinity

## Memory Issues with Large Datasets

**Error**: Script hanging and running out of memory during PCA computation on 15,000+ specimens

**Root Cause**: Manual matrix operations and eigendecomposition were memory-intensive and inefficient for large datasets

**Fix**: Replaced manual PCA implementation with sklearn's memory-optimized StandardScaler and PCA classes, which use efficient algorithms and memory management
