## MATLAB Cell Array Iteration Error

**Error**: TypeError: 'numpy.ndarray' object is not iterable in this context

**Root Cause**: scipy.io.loadmat loads MATLAB cell arrays as numpy object arrays, but direct iteration doesn't work as expected.

**Fix**: Access cell contents using array indexing: `spike_times_cell[0, i].flatten()` instead of direct iteration over the cell array.

## Array Dimension Mismatch Error  

**Error**: ValueError: x and y arrays must have at least 1 dimension

**Root Cause**: MATLAB arrays loaded with scipy.io can have unexpected singleton dimensions or be 0-dimensional after .flatten().

**Fix**: Use np.squeeze() to remove singleton dimensions and add explicit dimension checks with reshaping for expected array shapes.

## Quality Check Logic Error

**Error**: All trials incorrectly flagged despite passing individual quality metrics

**Root Cause**: Numpy boolean results not properly converted to Python bools, causing unexpected behavior in boolean logic operations.

**Fix**: Explicitly convert numpy boolean results using bool() function: `high_fr_flag = bool(np.any(firing_rates > 200))` to ensure proper boolean logic evaluation.
