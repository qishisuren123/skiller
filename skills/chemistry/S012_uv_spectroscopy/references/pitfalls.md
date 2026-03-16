# Common Pitfalls in UV-Vis Peak Analysis

## Peak Width Array Dimension Error

**Error**: `ValueError: array length of 'peaks' must be 1-D`

**Root Cause**: Passing individual peak indices as lists `[peak_idx]` to `peak_widths()` instead of processing all peaks together.

**Fix**: Pass the complete peaks array to `peak_widths()` once, then index the results for each peak using `widths[i]`.

## String Data Type Integration Error

**Error**: `numpy.core._exceptions._UFuncTypeError: ufunc 'add' did not contain a loop with signature matching types (dtype('<U32'), dtype('<U32'))`

**Root Cause**: CSV data loaded as strings instead of numeric values, causing integration functions to fail.

**Fix**: Use `pd.to_numeric(df[col], errors='coerce')` to convert all columns to numeric, then `dropna()` to remove invalid entries.

## Negative Peak Areas

**Error**: Peak area calculations returning negative values for absorption peaks.

**Root Cause**: Integrating raw absorbance values without baseline correction, leading to negative areas when baseline is not at zero.

**Fix**: Calculate linear baseline between peak boundaries and subtract before integration: `corrected_absorbance = peak_absorbances - baseline`.

## Zero Width Peak Crash

**Error**: `peak 32 has a width of 0` causing `peak_widths()` to fail.

**Root Cause**: Very noisy data creates sharp spikes that are only 1-2 data points wide, resulting in zero-width peaks.

**Fix**: Add width validation `if widths[i] < 0.5: continue` to skip degenerate peaks that are too narrow to be real absorption features.
