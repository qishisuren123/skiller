# Spike-Behavior-Organize: Common Pitfalls

This document catalogs eight frequently encountered pitfalls when working with
multi-format neural data, along with their root causes and fixes.

---

## Pitfall 1: MATLAB Struct `[0,0]` Unpacking

### Error
```
TypeError: 'numpy.void' object is not subscriptable
```
or accessing a field returns a single-element structured array instead of the
expected data.

### Root Cause
`scipy.io.loadmat` with `struct_as_record=True` returns MATLAB structs as
NumPy structured arrays of shape `(1, 1)`.  Attempting to access fields
directly on the outer array fails because the data lives one level deeper.
Without `[0, 0]`, you get the container, not the contents.

### Fix
Always unwrap with `[0, 0]` (for 2-D) or `[0]` (for 1-D) before accessing
field names via `dtype.names`.

### Code
```python
raw = loadmat(filepath, squeeze_me=False, struct_as_record=True)
struct_arr = raw['xds']                # shape (1, 1), dtype with named fields
xds = struct_arr[0, 0]                 # now a numpy.void with accessible fields
field_names = xds.dtype.names           # ('spike_times', 'cursor_vel', ...)
cursor_vel = np.asarray(xds['cursor_vel']).squeeze()
```

---

## Pitfall 2: NWB VectorIndex Spike Extraction

### Error
```
IndexError: index out of bounds
```
or getting concatenated spike times for all units instead of per-unit arrays.

### Root Cause
NWB stores spike times in a `VectorData` column backed by a `VectorIndex`.
Directly slicing `units['spike_times'].data[:]` returns a flat concatenation
of all units' spikes.  The `VectorIndex` maps which elements belong to which
unit, and manual slicing of the index is error-prone (off-by-one on the first
unit which has no preceding boundary).

### Fix
Use the high-level API: `units.get_unit_spike_times(idx)` which handles the
VectorIndex lookup correctly for every unit, including unit 0.

### Code
```python
spike_times = []
n_units = len(nwbfile.units)
for idx in range(n_units):
    st = nwbfile.units.get_unit_spike_times(idx)
    spike_times.append(np.asarray(st, dtype=np.float64))
```

---

## Pitfall 3: NWB Behavior Data Location (processing vs acquisition)

### Error
```
KeyError: 'behavior'
```
when accessing `nwbfile.processing['behavior']`.

### Root Cause
There is no single standard location for behavior data in NWB files.  Some
datasets (e.g., Dandiset 000121) store it under `processing['behavior']` as
`TimeSeries` or within a `Position` container holding `SpatialSeries`.  Others
(e.g., Dandiset 000070) store it directly in `acquisition`.  Code that only
checks one location silently misses the data.

### Fix
Check `processing['behavior']` first; if empty or absent, fall back to
`acquisition`.  Within the behavior processing module, iterate over
`data_interfaces` and also check for `SpatialSeries` inside `Position`
containers.

### Code
```python
behavior = {}

# Primary: processing module
if 'behavior' in nwbfile.processing:
    beh_module = nwbfile.processing['behavior']
    for name in beh_module.data_interfaces:
        ts = beh_module.data_interfaces[name]
        if hasattr(ts, 'data') and hasattr(ts, 'timestamps'):
            behavior[name] = (np.asarray(ts.data[:]), np.asarray(ts.timestamps[:]))
        elif hasattr(ts, 'spatial_series'):       # Position container
            for ss_name, ss in ts.spatial_series.items():
                behavior[ss_name] = (np.asarray(ss.data[:]), np.asarray(ss.timestamps[:]))

# Fallback: acquisition
if not behavior:
    for name in nwbfile.acquisition:
        ts = nwbfile.acquisition[name]
        if hasattr(ts, 'data') and hasattr(ts, 'timestamps'):
            behavior[name] = (np.asarray(ts.data[:]), np.asarray(ts.timestamps[:]))
```

---

## Pitfall 4: Trial Outcome Field Naming Differences

### Error
Filtering silently keeps zero trials (empty output) or keeps all trials
including failures.

### Root Cause
Different datasets use different field names and value conventions for trial
outcomes:

| Dataset     | Field      | Success value | Type         |
|-------------|------------|---------------|--------------|
| XDS         | `result`   | `"R"`         | MATLAB char  |
| PyalData    | `result`   | `1`           | numeric      |
| NWB 000121  | `outcome`  | `"success"`   | string       |
| NWB 000070  | (none)     | (none)        | no filtering |

Additionally, MATLAB char values may arrive as byte-strings (`b'R'`) after
`loadmat`, causing `== 'R'` comparisons to fail silently.

### Fix
Maintain a lookup dictionary (`SUCCESS_MARKERS`) mapping source types to
`(field_name, success_value)`.  Decode byte-strings before comparison.

### Code
```python
SUCCESS_MARKERS = {
    'xds':       ('result',  'R'),
    'pyaldata':  ('result',  1),
    'nwb_000121':('outcome', 'success'),
    'nwb_000070':(None,      None),        # no outcome field
}

field_name, success_value = SUCCESS_MARKERS[source_type]
if field_name is not None and field_name in df.columns:
    col = df[field_name]
    if col.dtype == object:   # handle byte-strings from MATLAB
        col = col.apply(lambda x: x.decode('utf-8').strip() if isinstance(x, bytes) else str(x).strip())
    mask = col == success_value
    df = df[mask]
```

---

## Pitfall 5: Time Alignment with Different Sampling Rates

### Error
Shape mismatches like:
```
ValueError: operands could not be broadcast together with shapes (1500,2) (3000,2)
```

### Root Cause
Behavior signals may be sampled at a different rate than the target bin size.
For example, cursor position at 1 kHz with 20 ms bins gives 50x more behavior
samples than bins.  Directly stacking them with binned spikes produces shape
mismatches.

Also, behavior timestamps may not align exactly with spike bin edges, causing
off-by-one-sample errors when naively slicing by index.

### Fix
Always resample behavior onto the target bin centers using interpolation rather
than index-based slicing.  Use `scipy.interpolate.interp1d` with
`fill_value='extrapolate'` for safety at boundaries.

### Code
```python
from scipy.interpolate import interp1d

def resample_behavior(data, timestamps, target_centers):
    """data: (T_orig, D), timestamps: (T_orig,), target_centers: (N_bins,)"""
    n_dims = data.shape[1] if data.ndim > 1 else 1
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    result = np.zeros((len(target_centers), n_dims))
    for d in range(n_dims):
        f = interp1d(timestamps, data[:, d], kind='linear',
                     fill_value='extrapolate', assume_sorted=True)
        result[:, d] = f(target_centers)
    return result
```

---

## Pitfall 6: Behavior Data In-Place Modification Bug

### Error
Subtle data corruption: the same behavior array is mutated across trials, so
later trials see smoothed/modified data from earlier trials.

### Root Cause
When slicing a NumPy array (e.g., `cursor_vel[mask, :]`), the result may be a
view rather than a copy.  Passing this view to `gaussian_filter1d` or
`np.gradient` with `out=` overwrites the original data in memory.  Subsequent
trials that overlap in time will read corrupted values.

### Fix
Always copy data before modifying it.  In `compute_kinematics`, the first line
after receiving input should be `data = data.copy()`.

### Code
```python
def compute_kinematics(data, data_type, bin_size_s, smooth_sigma=2.0):
    if data.ndim == 1:
        data = data.reshape(-1, 1)

    # CRITICAL: copy to avoid mutating caller's array
    data = data.copy()

    if smooth_sigma > 0:
        for d in range(data.shape[1]):
            data[:, d] = gaussian_filter1d(data[:, d], sigma=smooth_sigma)
    # ... differentiation / integration ...
```

---

## Pitfall 7: PyalData Struct Array Traversal

### Error
```
IndexError: index 0 is out of bounds for axis 0 with size 0
```
or only the first trial is processed.

### Root Cause
PyalData `.mat` files store trials as a MATLAB struct array.  After `loadmat`,
this becomes a NumPy structured array that can have shape `(N, 1)`, `(1, N)`,
or even `(N,)` depending on the MATLAB version and save options.  Code that
assumes a specific shape (e.g., iterating `struct_arr[0, :]`) fails when the
shape is `(N, 1)`.

Additionally, `squeeze_me=True` can collapse scalar fields unpredictably,
turning a `(1, 1)` array into a scalar that loses its `dtype.names`.

### Fix
Use `squeeze_me=False` and manually handle both orientations:

### Code
```python
raw = loadmat(filepath, squeeze_me=False, struct_as_record=True)
struct_arr = raw['trial_data']

# Normalize to 1-D array of struct elements
if struct_arr.ndim == 2:
    if struct_arr.shape[0] == 1:
        struct_arr = struct_arr[0, :]     # (1, N) -> (N,)
    elif struct_arr.shape[1] == 1:
        struct_arr = struct_arr[:, 0]     # (N, 1) -> (N,)
    else:
        struct_arr = struct_arr.ravel()   # unusual but safe
else:
    struct_arr = struct_arr.ravel()

n_trials = len(struct_arr)
for i in range(n_trials):
    trial = struct_arr[i]                 # numpy.void with named fields
    spikes = np.asarray(trial['M1_spikes']).squeeze()
```

---

## Pitfall 8: Multi-Brain-Area Spike Field Naming (M1_spikes, PMd_spikes)

### Error
Only one brain area's spikes appear in the output, or the unit count is
unexpectedly low.

### Root Cause
PyalData files from multi-electrode recordings store spike counts in separate
fields per brain area: `M1_spikes`, `PMd_spikes`, `S1_spikes`, etc.  Code
that hard-codes a single field name like `spikes` or `M1_spikes` will miss
other areas.

The naming convention is `<area>_spikes`, but the exact area names vary by
dataset (e.g., `MC_spikes`, `PMd_spikes`, `area2_spikes`).

### Fix
Auto-detect all spike fields by pattern-matching on `*spikes*` (case-insensitive),
then merge them with `np.hstack` along the unit axis.  Preserve the original
field names as metadata so that downstream analyses can recover which columns
belong to which brain area.

### Code
```python
field_names = struct_arr.dtype.names
spike_field_names = [f for f in field_names if 'spikes' in f.lower()]
# e.g., ['M1_spikes', 'PMd_spikes']

for i in range(n_trials):
    trial = struct_arr[i]
    parts = []
    for sf in spike_field_names:
        arr = np.asarray(trial[sf]).squeeze()
        if arr.ndim == 1:
            arr = arr.reshape(-1, 1)     # single unit -> column vector
        parts.append(arr)                # each is (N_bins, N_units_area)

    merged_spikes = np.hstack(parts)     # (N_bins, total_units)

# Store field mapping for downstream use
unit_area_map = {}
offset = 0
for sf in spike_field_names:
    n_units_area = parts_dict[sf].shape[1]
    area_name = sf.replace('_spikes', '')
    for u in range(n_units_area):
        unit_area_map[offset + u] = area_name
    offset += n_units_area
```
