## Missing scipy Dependency

**Error**: `ModuleNotFoundError: No module named 'scipy'`

**Root Cause**: Script imported scipy.interpolate but didn't actually use it for calculations.

**Fix**: Removed unnecessary scipy import and implemented yield strength calculation using pure numpy operations.

## JSON Serialization of NaN Values

**Error**: `json.decoder.JSONDecodeError: Out of range float values are not JSON compliant`

**Root Cause**: Numpy NaN and infinity values cannot be directly serialized to JSON format.

**Fix**: Created safe_float() function to convert numpy values to Python floats and handle NaN/inf by converting to null.

## Unrealistic Elastic Modulus Values

**Error**: Calculated elastic modulus values were inconsistent and unrealistically high.

**Root Cause**: Linear regression was not constrained to pass through origin, and fitting range was too large.

**Fix**: Modified calculation to use least squares through origin and reduced strain range for fitting to ensure linear region.

## Array Dimension Mismatch in Plotting

**Error**: `ValueError: x and y must have same first dimension, but have shapes (1000,) and (0,)`

**Root Cause**: For very small strain ranges (brittle materials), curve generation created empty stress arrays due to improper yield strain adaptation.

**Fix**: Added special handling for brittle materials with linear-only behavior and proper array validation before plotting.

## Hardcoded Offset Line Range

**Error**: Offset line extended beyond actual data range in plots, causing visual confusion.

**Root Cause**: Offset line range was hardcoded regardless of actual maximum strain in dataset.

**Fix**: Made offset line range adaptive to actual data bounds, ensuring it never extends beyond the strain range.
