## File Creation Errors

**Error**: FileNotFoundError when saving to nested directory paths
**Root Cause**: Output directories don't exist and matplotlib/json can't create them automatically
**Fix**: Use Path.mkdir(parents=True, exist_ok=True) before any file operations

## Incorrect Flow Patterns

**Error**: Positive flow values during expiration phase in synthetic data
**Root Cause**: Mathematical error in exponential decay calculation for expiratory flow
**Fix**: Use negative peak_exp_flow value (-8.0) and proper exponential decay formula

## Unrealistic Parameter Values

**Error**: FEV1 consistently 0.000L and FVC values too low (0.5L vs expected 3-5L)
**Root Cause**: Incorrect volume calculations and wrong phase identification in parameter functions
**Fix**: Fix volume integration, use proper start/end point detection, and add time-based indexing

## Performance Issues with Large Datasets

**Error**: Script hangs during FEV1 calculation with large n_points values
**Root Cause**: Inefficient np.argmin(np.abs(time - target)) operations on large arrays
**Fix**: Use sampling rate-based indexing and vectorized operations instead of time searches
