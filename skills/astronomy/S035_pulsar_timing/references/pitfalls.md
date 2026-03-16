# Array Shape Mismatch in Curve Fitting

**Error**: ValueError: operands could not be broadcast together with shapes (1247,) (45,)

**Root Cause**: When filtering for lowest frequency data, pulse_numbers array was calculated for all observations but TOA values were only from the filtered subset, causing shape mismatch in curve_fit.

**Fix**: Ensure pulse_numbers calculation is performed only on the filtered low_freq_data subset to match array dimensions.

# Type Error in Mathematical Operations

**Error**: TypeError: can't multiply sequence by non-int of type 'float'

**Root Cause**: DataFrame iterrows() returns pandas Series objects that cannot be directly used in mathematical operations with the quadratic timing model function.

**Fix**: Add explicit float() conversions when extracting values from DataFrame rows to ensure scalar arithmetic operations.

# Missing Frequency Band Statistics

**Error**: Empty frequency_band_stats dictionary in output JSON despite multi-frequency data

**Root Cause**: Incorrect nested dictionary structure where frequency_band_stats was created under residual_statistics but accessed at the top level of stats_dict.

**Fix**: Create frequency_band_stats as a separate dictionary and assign it directly to the top level of stats_dict structure.
