# scipy.io.loadmat - Load MATLAB files
loadmat(filename) -> dict
# Returns dictionary with variable names as keys

# scipy.interpolate.interp1d - 1D interpolation
interp1d(x, y, axis=0, kind='linear', bounds_error=False, fill_value=np.nan)
# x: input coordinates, y: input values
# axis: interpolation axis, kind: interpolation method
# bounds_error: raise error on out-of-bounds, fill_value: value for out-of-bounds

# h5py.File - HDF5 file operations
h5py.File(filename, 'w') -> File object
file.create_group(name) -> Group object
group.create_dataset(name, data=array) -> Dataset object
group.attrs[key] = value  # Set attributes

# numpy.histogram - Bin data
np.histogram(data, bins=edges) -> (counts, bin_edges)
# data: input data, bins: bin edges or number of bins

# numpy array operations
np.where(condition) -> indices where condition is True
np.linspace(start, stop, num) -> evenly spaced numbers
np.ceil(x) -> ceiling function
