# Key Libraries and Methods

## h5py
- `h5py.File(filepath, 'r')`: Open HDF5 file for reading
- `file.visititems(visitor)`: Traverse all items in HDF5 file
- `isinstance(obj, h5py.Dataset)`: Check if object is a dataset
- `dataset.shape`: Get dataset dimensions
- `dataset.dtype`: Get dataset data type

## scipy.io
- `scipy.io.loadmat(filepath)`: Load MATLAB file (v7.2 and earlier)
- Raises `NotImplementedError` for MATLAB v7.3 files

## numpy
- `np.integer`, `np.floating`: NumPy numeric types
- `data.dtype == 'object'`: Check for object arrays (cell arrays)

## os/pathlib
- `os.path.abspath()`: Convert to absolute path
- `os.path.relpath(path, start)`: Get relative path
- `os.walk()`: Recursive directory traversal
