# SKILL: Neural Data Trial-Based HDF5 Converter

## Overview
This tool converts MATLAB neural spike and behavior data into a standardized HDF5 format organized by trials. It bins spike times, resamples behavior data, and performs quality checks to ensure data integrity for downstream neural analysis pipelines.

## Step-by-Step Workflow

1. **Parse Arguments & Load Data**
   - Use argparse to handle CLI arguments (--input, --output, --bin-size)
   - Load MATLAB file using scipy.io.loadmat with squeeze_me=True
   - Extract all required arrays and validate their dimensions

2. **Filter Successful Trials**
   - Create boolean mask where trial_success == True
   - Apply mask to trial_start_times and trial_end_times
   - Store filtered trial indices for reference

3. **Process Each Trial**
   - For each successful trial, extract time window [start, end]
   - Create uniform time bins: np.arange(start, end + bin_size, bin_size)
   - Calculate bin centers for timestamp reference

4. **Bin Spike Data**
   - For each unit, filter spikes within trial window
   - Use np.histogram with bins from step 3 to count spikes per bin
   - Stack all units to create (n_bins, n_units) array

5. **Resample Behavior Data**
   - Extract behavior segment using time_frame indices within trial
   - Use scipy.interpolate.interp1d to create interpolator
   - Evaluate at bin centers to match spike data temporal resolution

6. **Quality Control**
   - Calculate firing rates: spike_counts / bin_size
   - Flag if any unit exceeds 200 Hz threshold
   - Check for NaN values in interpolated behavior

7. **Write HDF5 Output**
   - Create groups for each trial: /trial_0000, /trial_0001, etc.
   - Store datasets: spikes, behavior, timestamps
   - Add quality flag as attribute if issues detected

## Common Pitfalls & Solutions

1. **MATLAB Cell Array Handling**
   - **Issue**: spike_times loads as nested numpy arrays, not a clean cell array
   - **Solution**: Access cells with spike_times[0, unit_idx].flatten() and handle empty cells

2. **Time Alignment Errors**
   - **Issue**: Behavior timestamps don't fully cover trial period
   - **Solution**: Use extrapolation='fill' with fill_value=np.nan in interpolator, then check for NaNs

3. **Memory Overflow with Large Files**
   - **Issue**: Loading entire .mat file exhausts memory
   - **Solution**: Use h5py to read .mat files in v7.3 format, or process trials in chunks

4. **Bin Edge Artifacts**
   - **Issue**: Last bin may be partial, causing rate calculation errors
   - **Solution**: Exclude last bin if end time doesn't align with bin_size grid

5. **Unit Indexing Confusion**
   - **Issue**: MATLAB 1-indexing vs Python 0-indexing causes off-by-one errors
   - **Solution**: Always use 0-based indexing and validate array shapes match expected counts

## Error Handling Tips

- **Wrap file I/O** in try-except blocks to handle missing files gracefully
- **Validate array shapes** immediately after loading to catch malformed data early
- **Use assertions** for critical assumptions (e.g., assert len(trial_start_times) == len(trial_success))
- **Log warnings** for quality issues but continue processing unless data is corrupted
- **Implement --dry-run** option to validate input without writing output
- **Close HDF5 files** in finally blocks to prevent corruption on errors

## Reference Code Snippet

```python
def process_trial(spike_times, cursor_vel, time_frame, start_time, end_time, bin_size):
    """Core algorithm for processing a single trial"""
    # Create time bins
    bins = np.arange(start_time, end_time + bin_size, bin_size)
    bin_centers = bins[:-1] + bin_size / 2
    n_bins = len(bin_centers)
    n_units = spike_times.shape[1]
    
    # Bin spikes
    spike_counts = np.zeros((n_bins, n_units))
    for unit_idx in range(n_units):
        unit_spikes = spike_times[0, unit_idx].flatten()
        # Filter spikes within trial
        trial_spikes = unit_spikes[(unit_spikes >= start_time) & 
                                   (unit_spikes < end_time)]
        # Histogram counts
        counts, _ = np.histogram(trial_spikes, bins=bins)
        spike_counts[:, unit_idx] = counts
    
    # Resample behavior
    trial_mask = (time_frame >= start_time) & (time_frame <= end_time)
    trial_time = time_frame[trial_mask]
    trial_behavior = cursor_vel[trial_mask, :]
    
    # Interpolate to bin centers
    interp_func = interp1d(trial_time, trial_behavior, axis=0, 
                          bounds_error=False, fill_value=np.nan)
    resampled_behavior = interp_func(bin_centers)
    
    # Quality checks
    max_rate = np.max(spike_counts) / bin_size
    has_nan = np.any(np.isnan(resampled_behavior))
    quality_flag = (max_rate > 200) or has_nan
    
    return spike_counts, resampled_behavior, bin_centers, quality_flag
```