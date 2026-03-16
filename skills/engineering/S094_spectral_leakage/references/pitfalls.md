# Array Broadcasting Error
**Error**: ValueError: operands could not be broadcast together with shapes (2000,) (2000,)
**Root Cause**: Inconsistent data types between signal and window arrays causing broadcasting failure
**Fix**: Added explicit dtype casting to np.float64 and array flattening using asarray() and flatten()

# Division by Zero in Logarithm
**Error**: RuntimeWarning: divide by zero encountered in log10
**Root Cause**: Zero or very small values in normalized magnitude causing log10(0)
**Fix**: Added maximum clamping using np.maximum(normalized_magnitude, 1e-12) before logarithm calculation

# Empty Side Lobe Region
**Error**: IndexError: index 0 is out of bounds for axis 0 with size 0
**Root Cause**: right_null index exceeding array bounds creating empty slice for side_lobe_region
**Fix**: Added bounds checking before array slicing and default value assignment when no side lobes detected

# Window Power Normalization
**Error**: Division by zero in PSD normalization when window power is zero
**Root Cause**: Pathological window functions with zero total power
**Fix**: Added conditional check for window_power > 0 before normalization division
