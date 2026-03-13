# h5py - HDF5 for Python
h5py.File(filename, mode='r')  # Open HDF5 file
file.visititems(func)          # Traverse all items in file
isinstance(obj, h5py.Dataset)  # Check if object is dataset
dataset.shape                  # Tuple of dataset dimensions
dataset.dtype                  # NumPy dtype of dataset

# scipy.io - MATLAB file I/O
scipy.io.loadmat(filename, struct_as_record=False, squeeze_me=False)
# Returns dict of variable_name: array pairs
# Raises NotImplementedError for MATLAB v7.3 files

# pathlib.Path - Modern path handling
Path(directory).glob('**/*.h5')  # Recursive file search
path.suffix                      # File extension
path.stat().st_size             # File size in bytes
os.path.relpath(path, start)    # Relative path calculation
