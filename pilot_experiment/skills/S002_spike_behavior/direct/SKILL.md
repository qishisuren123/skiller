# Neural Data Trial Standardization

## Overview
This skill standardizes neural spike and behavior data from MATLAB files into a unified trial-based HDF5 format with consistent temporal binning and quality validation for neuroscience analysis pipelines.

## Workflow
1. Parse command-line arguments for input .mat file, output .h5 file, and bin size parameters
2. Load MATLAB data and extract spike times, behavior data, and trial metadata using scipy.io
3. Filter trials to include only successful trials based on trial_success boolean array
4. For each successful trial, create uniform time bins from trial start to end using specified bin size
5. Bin spike data using np.histogram for each unit and interpolate behavior data to bin centers
6. Perform quality checks: flag trials with firing rates >200Hz or NaN behavior values
7. Write structured HDF5 output with trial-specific groups containing spikes, behavior, and timestamps

## Common Pitfalls
- **MATLAB cell array handling**: Use `.flatten()` and check for empty cells when processing spike_times cell arrays, as some units may have no spikes in certain periods
- **Time alignment errors**: Ensure trial start/end times are within the bounds of time_frame array before interpolation to avoid extrapolation artifacts
- **Bin edge vs center confusion**: Use `bins[:-1] + bin_size/2` for bin centers when interpolating behavior data to match histogram bin assignments
- **Memory issues with large datasets**: Process trials sequentially and use chunked HDF5 writing for datasets with thousands of trials
- **Empty trial handling**: Check for trials shorter than one bin duration and either skip or pad appropriately to avoid zero-length arrays

## Error Handling
- Validate input file exists and contains required fields before processing
- Handle empty spike trains gracefully by creating zero-filled arrays with correct dimensions
- Catch interpolation errors when behavior data has gaps and implement forward-fill or linear interpolation fallbacks
- Implement HDF5 write error recovery with temporary file cleanup on failure

## Quick Reference
