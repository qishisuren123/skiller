#!/usr/bin/env python3
import argparse
import numpy as np
import h5py
from scipy.io import loadmat
from scipy.interpolate import interp1d

def detect_spike_time_units(spike_times, trial_start_times, trial_end_times):
    """Detect if spike times are in seconds or milliseconds by checking reasonable ranges"""
    sample_spikes = []
    for unit_idx in range(min(3, spike_times.shape[1])):
        unit_spikes = spike_times[0, unit_idx].flatten()
        if len(unit_spikes) > 0:
            sample_spikes.extend(unit_spikes[:100])
    
    if len(sample_spikes) == 0:
        return 1.0
    
    sample_spikes = np.array(sample_spikes)
    
    print(f"Sample spike times range: {np.min(sample_spikes):.3f} to {np.max(sample_spikes):.3f}")
    print(f"Trial time range: {np.min(trial_start_times):.3f} to {np.max(trial_end_times):.3f}")
    
    if np.max(sample_spikes) > 10 * np.max(trial_end_times):
        print("Detected: Spike times appear to be in milliseconds, converting to seconds")
        return 0.001
    else:
        print("Detected: Spike times appear to be in seconds")
        return 1.0

def process_trial(h5_file, original_idx, new_idx, spike_times, cursor_vel, time_frame, 
                 trial_start, trial_end, bin_size, spike_time_conversion, min_duration):
    # Check minimum duration
    trial_duration = trial_end - trial_start
    if trial_duration < min_duration:
        print(f"Skipping trial {original_idx}: too short ({trial_duration:.3f}s < {min_duration:.3f}s)")
        return False, True
    
    # Check behavior data coverage
    behavior_start, behavior_end = np.min(time_frame), np.max(time_frame)
    if trial_start < behavior_start or trial_end > behavior_end:
        print(f"Skipping trial {original_idx}: extends beyond behavior data timeframe")
        return False, False
    
    # Calculate bins
    n_bins = int(np.ceil(trial_duration / bin_size))
    actual_bin_size = trial_duration / n_bins
    
    bin_edges = np.linspace(trial_start, trial_end, n_bins + 1)
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    
    # Bin spike data
    n_units = spike_times.shape[1]
    spike_counts = np.zeros((n_bins, n_units))
    
    for unit_idx in range(n_units):
        unit_spikes = spike_times[0, unit_idx].flatten() * spike_time_conversion
        trial_spikes = unit_spikes[(unit_spikes >= trial_start) & (unit_spikes <= trial_end)]
        counts, _ = np.histogram(trial_spikes, bins=bin_edges)
        spike_counts[:, unit_idx] = counts
    
    # Resample behavior data
    trial_mask = (time_frame >= trial_start) & (time_frame <= trial_end)
    trial_time = time_frame[trial_mask]
    trial_vel = cursor_vel[trial_mask]
    
    if len(trial_time) < 2:
        print(f"Skipping trial {original_idx}: insufficient behavior data points ({len(trial_time)})")
        return False, False
    
    interp_func = interp1d(trial_time, trial_vel, axis=0, kind='linear', 
                          bounds_error=False, fill_value=np.nan)
    resampled_vel = interp_func(bin_centers)
    
    # Quality checks
    firing_rates = spike_counts / actual_bin_size
    high_fr_flag = np.any(firing_rates > 200)
    nan_behavior_flag = np.any(np.isnan(resampled_vel))
    
    if high_fr_flag or nan_behavior_flag:
        print(f"Warning: Trial {original_idx} flagged - High FR: {high_fr_flag}, NaN behavior: {nan_behavior_flag}")
    
    # Save to HDF5
    trial_group = h5_file.create_group(f'trial_{new_idx:04d}')
    trial_group.create_dataset('spikes', data=spike_counts)
    trial_group.create_dataset('behavior', data=resampled_vel)
    trial_group.create_dataset('timestamps', data=bin_centers)
    trial_group.attrs['original_trial_index'] = original_idx
    trial_group.attrs['trial_duration'] = trial_duration
    trial_group.attrs['actual_bin_size'] = actual_bin_size
    trial_group.attrs['high_firing_rate'] = high_fr_flag
    trial_group.attrs['nan_behavior'] = nan_behavior_flag
    
    return True, False

def main():
    parser = argparse.ArgumentParser(description='Standardize neural spike and behavior data into HDF5')
    parser.add_argument('--input', required=True, help='Input MATLAB .mat file')
    parser.add_argument('--output', required=True, help='Output HDF5 file')
    parser.add_argument('--bin-size', type=float, default=0.02, help='Bin size in seconds (default: 0.02)')
    parser.add_argument('--min-duration', type=float, default=0.1, help='Minimum trial duration in seconds (default: 0.1)')
    
    args = parser.parse_args()
    
    # Load MATLAB data
    print(f"Loading data from {args.input}")
    data = loadmat(args.input)
    
    spike_times = data['spike_times']
    cursor_vel = data['cursor_vel']
    time_frame = data['time_frame'].flatten()
    trial_start_times = data['trial_start_times'].flatten()
    trial_end_times = data['trial_end_times'].flatten()
    trial_success = data['trial_success'].flatten()
    
    # Detect and convert spike time units
    spike_time_conversion = detect_spike_time_units(spike_times, trial_start_times, trial_end_times)
    
    # Filter successful trials
    successful_trials = np.where(trial_success == True)[0]
    print(f"Processing {len(successful_trials)} successful trials out of {len(trial_success)} total")
    
    # Create HDF5 file
    with h5py.File(args.output, 'w') as f:
        valid_trial_count = 0
        short_trial_count = 0
        for original_idx in successful_trials:
            success, was_too_short = process_trial(f, original_idx, valid_trial_count, spike_times, cursor_vel, time_frame,
                         trial_start_times[original_idx], trial_end_times[original_idx], 
                         args.bin_size, spike_time_conversion, args.min_duration)
            if success:
                valid_trial_count += 1
            elif was_too_short:
                short_trial_count += 1
    
    print(f"Data saved to {args.output}")
    print(f"Valid trials: {valid_trial_count}")
    print(f"Skipped short trials: {short_trial_count}")
    print(f"Total processed: {valid_trial_count + short_trial_count}")

if __name__ == '__main__':
    main()
