# Neural Data Standardization Tool

## Overview
A Python CLI tool that converts MATLAB neural spike and behavior data into standardized trial-based HDF5 format. The tool bins spike times, resamples behavior data to matching time grids, and performs quality checks on neural firing rates and behavior data integrity.

## Workflow

1. **Parse Arguments & Load Data**
   - Parse CLI arguments for input/output files and bin size
   - Load MATLAB .mat file using scipy.io.loadmat
   - Extract spike times, behavior data, and trial information

2. **Filter Successful Trials**
   - Identify trials where trial_success == True
   - Create filtered arrays of start/end times for processing

3. **Process Each Trial**
   - Calculate trial duration and create uniform time bins
   - Generate bin centers for timestamp alignment

4. **Bin Spike Data**
   - For each neural unit, use np.histogram to bin spike times
   - Convert counts to firing rates (counts / bin_size)

5. **Resample Behavior Data**
   - Use scipy.interpolate to resample cursor velocity to bin centers
   - Handle edge cases where trial times exceed behavior recording

6. **Quality Control**
   - Flag trials with firing rates > 200 Hz in any unit
   - Flag trials containing NaN values in behavior data

7. **Write HDF5 Output**
   - Create trial groups (/trial_0001, /trial_0002, etc.)
   - Save spikes, behavior, and timestamps datasets per trial

## Common Pitfalls

1. **MATLAB Cell Array Handling**
   - *Problem*: scipy.io.loadmat loads cell arrays as object arrays with nested structure
   - *Solution*: Access with `spike_times[0, unit_idx][0]` to extract actual arrays

2. **Time Alignment Issues**
   - *Problem*: Trial times may extend beyond behavior recording duration
   - *Solution*: Clip trial times to behavior data bounds and use extrapolation in interpolation

3. **Empty Spike Trains**
   - *Problem*: Some units may have no spikes in certain trials, causing histogram errors
   - *Solution*: Check for empty arrays before binning and handle with zero-filled arrays

4. **HDF5 Dataset Naming**
   - *Problem*: Trial numbers need consistent formatting for proper sorting
   - *Solution*: Use zero-padded formatting: `f"trial_{trial_idx:04d}"`

5. **Memory Issues with Large Files**
   - *Problem*: Loading entire datasets into memory can cause crashes
   - *Solution*: Process trials sequentially and use chunked HDF5 writing

## Error Handling Tips

- Validate input file exists and is readable before processing
- Check for required fields in MATLAB structure
- Handle interpolation failures with try-catch and fallback values
- Verify HDF5 write permissions before starting processing
- Add progress indicators for long-running operations
- Log quality control failures with trial indices for debugging

## Reference Code

```python
import numpy as np
import h5py
from scipy.io import loadmat
from scipy.interpolate import interp1d

def process_trial(spike_times, cursor_vel, time_frame, start_time, end_time, bin_size):
    # Create time bins
    trial_duration = end_time - start_time
    n_bins = int(np.ceil(trial_duration / bin_size))
    bin_edges = np.linspace(0, trial_duration, n_bins + 1)
    bin_centers = bin_edges[:-1] + bin_size / 2
    
    # Bin spikes
    n_units = len(spike_times[0])
    spike_rates = np.zeros((n_bins, n_units))
    
    for unit_idx in range(n_units):
        unit_spikes = spike_times[0, unit_idx][0]  # Handle MATLAB cell array
        trial_spikes = unit_spikes[(unit_spikes >= start_time) & (unit_spikes < end_time)]
        trial_spikes_rel = trial_spikes - start_time  # Relative to trial start
        
        if len(trial_spikes_rel) > 0:
            counts, _ = np.histogram(trial_spikes_rel, bins=bin_edges)
            spike_rates[:, unit_idx] = counts / bin_size
    
    # Resample behavior
    interp_func = interp1d(time_frame, cursor_vel, axis=0, bounds_error=False, 
                          fill_value='extrapolate')
    behavior_resampled = interp_func(bin_centers + start_time)
    
    # Quality checks
    max_firing_rate = np.max(spike_rates)
    has_nan_behavior = np.any(np.isnan(behavior_resampled))
    quality_flag = max_firing_rate <= 200 and not has_nan_behavior
    
    return spike_rates, behavior_resampled, bin_centers, quality_flag
```