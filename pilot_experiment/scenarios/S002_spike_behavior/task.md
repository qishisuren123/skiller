Write a Python CLI script that standardizes neural spike and behavior data into a unified trial-based HDF5 file.

Input: A MATLAB .mat file containing:
- spike_times: a (1, N_units) cell array where each cell has sorted spike times (in seconds)
- cursor_vel: (T, 2) array of velocity data
- time_frame: (T,) array of time points
- trial_start_times: (N_trials,) array
- trial_end_times: (N_trials,) array
- trial_success: (N_trials,) boolean array

Requirements:
1. Use argparse: --input for .mat file, --output for .h5 file, --bin-size (default 0.02s)
2. Filter only successful trials (trial_success == True)
3. For each trial, bin spike times into uniform time bins using np.histogram
4. Resample behavior (velocity) to match bin centers using interpolation
5. Write HDF5 with structure: /trial_NNNN/spikes (n_bins, n_units), /trial_NNNN/behavior (n_bins, 2), /trial_NNNN/timestamps (n_bins,)
6. Add quality check: flag trials where any unit has firing rate > 200 Hz or behavior contains NaN
