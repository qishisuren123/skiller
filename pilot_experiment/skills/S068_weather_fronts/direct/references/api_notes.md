# Key Libraries for Weather Front Detection

## h5py - HDF5 File Operations
- `h5py.File(filename, 'r')`: Open HDF5 file for reading
- `file['dataset'][:]`: Read entire dataset into memory
- `file['dataset'][()]`: Read scalar dataset value

## scipy.ndimage - Image Processing for Meteorological Data
- `gaussian_filter(input, sigma)`: Apply Gaussian smoothing to temperature field
- `label(input, structure)`: Segment connected regions in binary front mask
- `find_objects(labeled_array)`: Find bounding boxes of labeled regions

## numpy - Gradient Calculations
- `np.gradient(array)`: Compute gradients using central differences
- `np.sqrt(x**2 + y**2)`: Calculate gradient magnitude
- `np.where(condition)`: Find indices where condition is True
- `np.meshgrid(x, y)`: Create coordinate grids for plotting

## matplotlib.pyplot - Meteorological Visualization
- `contourf(X, Y, Z, levels, cmap)`: Filled contour plot for temperature fields
- `contour(X, Y, Z, levels, colors)`: Line contours for front boundaries
- `colorbar(mappable, ax, label)`: Add color scale bar
