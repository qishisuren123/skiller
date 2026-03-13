# SKILL: Neural Spike and Behavior Data Standardization to HDF5

## Overview
This tool converts MATLAB `.mat` files containing neural spike recordings and behavioral data into a standardized trial-based HDF5 format. It bins spike times, resamples behavior data, and applies quality checks to ensure data integrity for downstream analysis.

## Workflow

### Step 1: Parse Command-Line Arguments
Use `argparse` to accept:
- `--input`: Path to MATLAB `.mat` file
- `--output`: Path to output HDF5 file
- `--bin-size`: Temporal bin width in seconds (default: 0.02s)

### Step 2: Load and Validate Input Data
- Load `.mat` file using `scipy.io.loadmat()`
- Extract spike_times (cell array), cursor_vel, time_frame, trial_start_times, trial_end_times, trial_success
- Verify all required fields exist and have expected shapes
- Filter to successful trials only using `trial_success == True`

### Step 3: Initialize HDF5 Output File
- Create output HDF5 file with `h5py.File()`
- Create root-level metadata group with bin_size and trial count attributes

### Step 4: Process Each Trial
For each successful trial:
- Extract trial time window: `[trial_start_times[i], trial_end_times[i]]`
- Generate bin edges: `np.arange(trial_start, trial_end + bin_size, bin_size)`
- Bin spike times for each unit using `np.histogram(spike_times, bins=bin_edges)`
- Resample behavior data to bin centers using `scipy.interpolate.interp1d()`

### Step 5: Quality Check
For each trial, verify:
- No unit exceeds 200 Hz firing rate: `(spike_count / trial_duration) <= 200`
- Behavior data contains no NaN values
- Flag failed trials with metadata attribute `quality_flag`

### Step 6: Write to HDF5
Create hierarchical structure:
```
/trial_0000/spikes       → (n_bins, n_units) spike counts
/trial_0000/behavior     → (n_bins, 2) resampled velocity
/trial_0000/timestamps   → (n_bins,) bin center times
/trial_0000/attrs        → quality_flag, duration
```

### Step 7: Log Summary Statistics
Print trial count, quality pass rate, and output file size.

---

## Common Pitfalls & Solutions

| Pitfall | Cause | Solution |
|---------|-------|----------|
| **MATLAB cell array indexing errors** | `scipy.io.loadmat()` returns nested lists/arrays; cell indexing differs from MATLAB | Flatten cell arrays: `spike_times = [np.array(st).flatten() for st in spike_times[0]]` |
| **Bin edge misalignment** | Spike times outside trial window or floating-point precision issues | Use `np.histogram(..., range=(trial_start, trial_end))` and ensure spike filtering: `spikes = spikes[(spikes >= trial_start) & (spikes <= trial_end)]` |
| **Interpolation fails on sparse behavior data** | Behavior time_frame may not align with trial boundaries | Clip behavior to trial window first: `mask = (time_frame >= trial_start) & (time_frame <= trial_end)` before interpolation |
| **Memory overflow on large files** | Processing all trials at once with large spike arrays | Process trials iteratively; use `h5py` chunking: `dataset.chunks = (100, n_units)` |
| **NaN propagation in resampling** | Extrapolation beyond behavior time range | Use `fill_value='extrapolate'` cautiously; better: clip trial times to behavior range |

---

## Error Handling Tips

1. **File I/O**: Wrap `scipy.io.loadmat()` and `h5py.File()` in try-except; provide clear error messages for missing files or corrupted data.
2. **Data validation**: Check array shapes immediately after loading; raise `ValueError` with expected vs. actual shapes.
3. **Spike filtering**: Silently skip units with zero spikes in a trial (avoid division by zero in firing rate calculation).
4. **Interpolation bounds**: Log warnings for trials where behavior time range doesn't fully cover spike times; use `kind='linear'` (most robust).
5. **HDF5 write failures**: Ensure output directory exists; catch `OSError` and suggest permission/disk space issues.

---

## Reference Code Snippet

```python
import numpy as np
from scipy.io import loadmat
from scipy.interpolate import interp1d
import h5py

def process_trial(spike_times_units, cursor_vel, time_frame, trial_start, trial_end, 
                  bin_size, trial_idx, output_file):
    """Process a single trial: bin spikes, resample behavior, quality check."""
    
    # Generate bin edges and centers
    bin_edges = np.arange(trial_start, trial_end + bin_size, bin_size)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    n_bins = len(bin_centers)
    
    # Bin spike times for each unit
    spike_counts = []
    for unit_spikes in spike_times_units:
        unit_spikes = np.array(unit_spikes).flatten()
        unit_spikes = unit_spikes[(unit_spikes >= trial_start) & (unit_spikes <= trial_end)]
        counts, _ = np.histogram(unit_spikes, bins=bin_edges)
        spike_counts.append(counts)
    spike_matrix = np.array(spike_counts).T  # (n_bins, n_units)
    
    # Resample behavior to bin centers
    behavior_mask = (time_frame >= trial_start) & (time_frame <= trial_end)
    behavior_times = time_frame[behavior_mask]
    behavior_data = cursor_vel[behavior_mask]
    
    f_interp = interp1d(behavior_times, behavior_data, axis=0, kind='linear', 
                        bounds_error=False, fill_value=np.nan)
    behavior_resampled = f_interp(bin_centers)  # (n_bins, 2)
    
    # Quality check
    trial_duration = trial_end - trial_start
    max_firing_rate = np.max(spike_counts / trial_duration)
    has_nan = np.any(np.isnan(behavior_resampled))
    quality_flag = (max_firing_rate <= 200) and (not has_nan)
    
    # Write to HDF5
    trial_group = output_file.create_group(f'trial_{trial_idx:04d}')
    trial_group.create_dataset('spikes', data=spike_matrix)
    trial_group.create_dataset('behavior', data=behavior_resampled)
    trial_group.create_dataset('timestamps', data=bin_centers)
    trial_group.attrs['quality_flag'] = quality_flag
    trial_group.attrs['duration'] = trial_duration
```