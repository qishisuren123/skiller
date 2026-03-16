## Argument Parsing Error

**Error**: TypeError: unsupported operand type(s) for *: 'NoneType' and 'int'

**Root Cause**: Arguments were not being parsed correctly due to missing type specifications in argparse setup.

**Fix**: Added explicit type specifications (type=int, type=float, type=str) to all argparse arguments and added input validation.

## FFT Amplitude Calculation Error

**Error**: Identified constituent amplitudes were approximately half the expected values from synthetic data generation.

**Root Cause**: Incorrect amplitude normalization in FFT analysis - was dividing by 2 twice instead of applying the correct 2/N factor for real signals.

**Fix**: Corrected amplitude calculation to `np.abs(fft_result) * 2.0 / len(tidal_heights_detrended)` and fixed phase extraction from complex FFT results.

## Frequency Resolution Issue

**Error**: No constituents identified with short duration datasets (1 day) even with low amplitude thresholds.

**Root Cause**: Insufficient frequency resolution with short time series - FFT resolution is 1/duration, so 1 day gives 24-hour resolution which cannot separate tidal constituents.

**Fix**: Added frequency resolution calculation, adaptive tolerance based on resolution, and warnings for short duration datasets. Recommended minimum 3 days for proper constituent separation.

## Memory Error with Fine Sampling

**Error**: MemoryError: Unable to allocate 1.26 GiB for array with fine sampling intervals.

**Root Cause**: Very fine sampling intervals (0.01 hours) create extremely large arrays that exceed available memory.

**Fix**: Added memory estimation function, hard limits on data points (500k) and memory usage (2GB), validation of sampling intervals, and subsampling for plotting large datasets.
