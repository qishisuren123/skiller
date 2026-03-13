# Neuroscience Data Formats Reference

## HDF5 Files (.h5, .hdf5)

HDF5 (Hierarchical Data Format version 5) stores data in a tree-like structure
of groups and datasets. In neuroscience, HDF5 is commonly used for large
time-series recordings.

### Structure

```
/                          (root group)
├── CellResp               Dataset: (N_neurons, N_timepoints), float32
├── CellRespAvr            Dataset: (N_neurons, N_timepoints_trial), float32
├── CellRespAvrZ           Dataset: (N_neurons, N_timepoints_trial), float32
├── CellRespZ              Dataset: (N_neurons, N_timepoints), float32
└── absIX                  Dataset: (N_neurons, 1), int32
```

### Reading with h5py

```python
import h5py
with h5py.File("TimeSeries.h5", "r") as f:
    for key in f:
        obj = f[key]
        if isinstance(obj, h5py.Dataset):
            print(f"{key}: shape={obj.shape}, dtype={obj.dtype}")
        elif isinstance(obj, h5py.Group):
            # Must recurse into groups
            pass
```

## MATLAB Files (.mat)

### v5/v7 Format (standard)

Read with `scipy.io.loadmat()`. Returns a dict with variable names as keys.
Always filter out internal keys: `__header__`, `__version__`, `__globals__`.

### v7.3 Format (HDF5-based)

When MATLAB saves with `-v7.3`, the resulting file is HDF5 internally.
`scipy.io.loadmat()` will fail. Detect and fall back to h5py:

```python
try:
    mat = scipy.io.loadmat(path)
except (NotImplementedError, ValueError, OSError):
    # v7.3 detected
    with h5py.File(path, "r") as f:
        ...
```

### Common MATLAB variables

| Variable | Description | Typical shape |
|----------|-------------|--------------|
| periods | Stimulus phase durations | (1, N_phases) |
| fpsec | Frame rate | scalar |
| numcell_full | Total neuron count | scalar |
| CellXYZ | Cell coordinates | (N_neurons, 3) |
| CellXYZ_norm | Normalized coordinates | (N_neurons, 3) |
| anat_stack | 3D anatomy volume | (H, W, D) |
| anat_yx | Top-down projection | (H, W, 3) |
| timelists | Stimulus time indices | cell array |
| Behavior_raw | Raw swim signals | (1, N_raw_timepoints) |
| Behavior_full | Processed behavior | (1, N_timepoints) |
