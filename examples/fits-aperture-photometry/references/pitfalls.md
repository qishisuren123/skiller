# Common Pitfalls and Solutions

## SEP Data Type Compatibility Error
**Error**: `ValueError: array dtype must be numpy.float32 or numpy.float64`
**Root Cause**: FITS data often comes with big-endian byte order or integer dtypes that SEP cannot handle
**Fix**: Always convert to little-endian float64: `data.astype('<f8')` and ensure C-contiguous arrays with `np.ascontiguousarray()`

## Photutils Position Format Error  
**Error**: `AttributeError: 'list' object has no attribute 'do_photometry'`
**Root Cause**: Photutils aperture_photometry expects positions as (x_array, y_array) tuple, not list of (x,y) pairs
**Fix**: Convert position lists to numpy arrays: `positions = (np.array(x_coords), np.array(y_coords))`

## WCS Coordinate Transformation Error
**Error**: Stars appearing outside image boundaries or coordinate conversion failures
**Root Cause**: Invalid WCS information or coordinate system mismatches
**Fix**: Validate WCS before use, filter stars within image bounds, handle transformation exceptions with try/catch blocks

## Sky Annulus Contamination Error
**Error**: Negative sky-subtracted fluxes or unrealistic magnitude values
**Root Cause**: Sky annulus overlapping with source aperture or contaminated by nearby stars
**Fix**: Ensure sky_inner > aperture_radius, use larger sky annuli for crowded fields, implement source masking in sky regions

## Missing FITS Metadata Error
**Error**: KeyError when accessing header values like EXPTIME, GAIN
**Root Cause**: Non-standard or missing FITS header keywords
**Fix**: Use header.get() with default values: `exptime = header.get('EXPTIME', 1.0)`, validate critical parameters before processing

## Curve of Growth Sampling Error
**Error**: Insufficient data points or noisy growth curves
**Root Cause**: Too few radial samples or faint stars with poor S/N
**Fix**: Use logarithmic radius spacing, require minimum brightness thresholds, smooth growth curves for aperture corrections
