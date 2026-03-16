# Common Pitfalls and Solutions

## Performance Issues with Manual Spherical Harmonics

**Error**: Code taking 10+ minutes for NSIDE=32 map
**Root Cause**: Using manual scipy.special.sph_harm() computation with O(N_pix × l_max²) complexity
**Fix**: Replace with healpy.map2alm() which uses optimized C++ libraries and completes in seconds

## Array Ambiguity in Conditional Logic

**Error**: "ValueError: The truth value of an array is ambiguous. Use a.any() or a.all()"
**Root Cause**: Using conditional `if m >= 0` with numpy arrays in spherical harmonic computation
**Fix**: Remove problematic conditional logic and use proper conjugate symmetry relations for negative m values

## Data Type Incompatibility in Plotting

**Error**: "TypeError: unsupported operand type(s) for *: 'numpy.int64' and 'NoneType'"
**Root Cause**: Array filtering creating incompatible data types or None values
**Fix**: Explicit type conversion to np.float64 and robust array validation before mathematical operations

## Incorrect Power Spectrum Array Indexing

**Error**: Many exact zero values in power spectrum output
**Root Cause**: Incorrect slicing of hp.alm2cl() output array - hp.alm2cl()[l] corresponds to multipole l
**Fix**: Proper array indexing: l_values = np.arange(2, len(cl_full)) and cl_output = cl_full[2:len(cl_full)]

## Missing Error Handling for Invalid Data

**Error**: Silent failures or crashes with corrupted input data
**Root Cause**: Insufficient validation of input arrays and intermediate results
**Fix**: Add comprehensive logging, array shape validation, and finite value checks throughout pipeline
