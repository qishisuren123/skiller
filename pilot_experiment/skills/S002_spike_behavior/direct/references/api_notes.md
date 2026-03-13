# scipy.io.loadmat
scipy.io.loadmat(file_name, squeeze_me=False)
# squeeze_me=False preserves original array dimensions from MATLAB

# numpy.histogram for spike binning
np.histogram(a, bins, range=None, density=False)
# Returns (hist, bin_edges) where hist has length len(bin_edges)-1

# numpy.interp for behavior resampling
np.interp(x, xp, fp, left=None, right=None)
# x: points to evaluate, xp: known x-coords, fp: known y-values

# h5py group and dataset creation
h5file.create_group(name)
group.create_dataset(name, data=array, compression='gzip')
group.attrs['key'] = value  # metadata storage

# Key array operations
array.flatten()  # Convert to 1D
np.arange(start, stop, step)  # Create uniform bins
np.column_stack([arr1, arr2])  # Combine arrays horizontally
np.where(condition)[0]  # Get indices where condition is True
