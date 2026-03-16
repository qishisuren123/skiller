# JSON Serialization Error

**Error**: `TypeError: Object of type ndarray is not JSON serializable`

**Root Cause**: Attempting to serialize numpy arrays directly to JSON without conversion, as JSON doesn't natively support numpy data types.

**Fix**: Implement recursive conversion function to transform numpy arrays to lists and numpy scalars to Python primitives before JSON serialization.

# Missing Coordinate Array Error  

**Error**: `ValueError: setting an array element with a sequence`

**Root Cause**: Incomplete coordinate array creation missing the y-coordinate, creating inconsistent array dimensions.

**Fix**: Ensure all coordinate arrays include complete [x, y, z] triplets when creating numpy arrays from atomic coordinates.

# Division by Zero in Angle Calculation

**Error**: `RuntimeWarning: invalid value encountered in true_divide` followed by `ValueError: math domain error`

**Root Cause**: Zero-length vectors in angle calculations when atoms have identical coordinates or extremely small distances.

**Fix**: Add vector magnitude validation before division and handle edge cases by returning NaN for invalid calculations with appropriate logging.
