## SVD Convergence Failure in Polynomial Fitting

**Error**: `numpy.linalg.LinAlgError: SVD did not converge in Linear Least Squares` when processing high-noise spectra (SNR < 10)

**Root Cause**: Large wavelength values (thousands of Angstroms) combined with high polynomial orders create ill-conditioned matrices that cause SVD decomposition to fail during least squares fitting.

**Fix**: Scale wavelength values by subtracting mean and dividing by standard deviation before polynomial fitting. Implement graceful degradation by reducing polynomial order when fits fail, with ultimate fallback to median continuum.

## Division by Zero in Continuum Normalization

**Error**: Runtime warnings and invalid results when continuum values approach zero

**Root Cause**: Fitted continuum can have negative or near-zero values, especially with noisy data or poor fits, leading to division by zero during normalization.

**Fix**: Replace zero or negative continuum values with median continuum value before division. Add validation checks to ensure continuum values are physically reasonable.

## Insufficient Data After Sigma Clipping

**Error**: Empty arrays or unreliable fits when too many points are rejected during iterative continuum fitting

**Root Cause**: Aggressive sigma clipping with very noisy data can reject most data points, leaving insufficient points for reliable polynomial fitting.

**Fix**: Add safety check to ensure at least 10% of original points remain after clipping. Stop iteration early if too few points remain and use current fit as final result.

## Invalid Equivalent Width Calculations

**Error**: NaN or negative equivalent width values for absorption lines

**Root Cause**: Sparse wavelength coverage around spectral lines or invalid normalized flux values (NaN/infinity) cause integration failures.

**Fix**: Validate finite values before integration, require minimum number of points in line region, and handle edge cases where lines fall outside wavelength coverage.
