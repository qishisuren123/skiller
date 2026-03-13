# Unit detection example
spike_time_conversion = detect_spike_time_units(spike_times, trial_start_times, trial_end_times)
unit_spikes = spike_times[0, unit_idx].flatten() * spike_time_conversion

# Robust interpolation with bounds checking
trial_mask = (time_frame >= trial_start) & (time_frame <= trial_end)
trial_time = time_frame[trial_mask]
trial_vel = cursor_vel[trial_mask]

if len(trial_time) >= 2:
    interp_func = interp1d(trial_time, trial_vel, axis=0, kind='linear', 
                          bounds_error=False, fill_value=np.nan)
    resampled_vel = interp_func(bin_centers)

# Spike binning with proper time conversion
for unit_idx in range(n_units):
    unit_spikes = spike_times[0, unit_idx].flatten() * spike_time_conversion
    trial_spikes = unit_spikes[(unit_spikes >= trial_start) & (unit_spikes <= trial_end)]
    counts, _ = np.histogram(trial_spikes, bins=bin_edges)
    spike_counts[:, unit_idx] = counts

# Quality checking and flagging
firing_rates = spike_counts / actual_bin_size
high_fr_flag = np.any(firing_rates > 200)
nan_behavior_flag = np.any(np.isnan(resampled_vel))

# HDF5 storage with metadata
trial_group = h5_file.create_group(f'trial_{new_idx:04d}')
trial_group.create_dataset('spikes', data=spike_counts)
trial_group.attrs['original_trial_index'] = original_idx
trial_group.attrs['trial_duration'] = trial_duration
