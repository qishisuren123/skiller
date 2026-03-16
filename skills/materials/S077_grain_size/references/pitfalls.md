## Argparse Attribute Error

**Error**: AttributeError: 'NoneType' object has no attribute 'split' when using multiple argument names

**Root Cause**: When defining argparse arguments with multiple names like `--diameters` and `--grain_diameters`, argparse can create naming conflicts without explicit destination specification

**Fix**: Add `dest='diameters'` parameter to explicitly define the attribute name: `parser.add_argument('--diameters', '--grain_diameters', dest='diameters', required=True)`

## JSON Serialization with Infinity

**Error**: JSON file corruption when coefficients contain infinity values from division by zero

**Root Cause**: Setting coefficients to `float('inf')` when D10 is zero creates values that cannot be serialized to valid JSON format

**Fix**: Use `None` instead of `float('inf')` for invalid coefficient calculations, which serializes properly as `null` in JSON

## Histogram Rendering Flat Distribution

**Error**: Histogram shows flat line with all zero bin counts despite valid data with normal distribution

**Root Cause**: Data type incompatibilities between numpy arrays and matplotlib, or automatic bin determination failing with the data range

**Fix**: Explicitly convert data to `np.float64` and use `np.linspace()` to create explicit bin edges: `bin_edges = np.linspace(np.min(plot_data), np.max(plot_data), 31)`

## Division by Zero in Coefficients

**Error**: ZeroDivisionError when calculating uniformity coefficient even with valid grain size data

**Root Cause**: Zero or negative values in the dataset cause D10 percentile to be zero, leading to division by zero in Cu = D60/D10 calculation

**Fix**: Implement data cleaning to remove invalid values before percentile calculations and add validation checks before division operations
