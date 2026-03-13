import argparse
import numpy as np
import scipy.io
import h5py
import sys
from pathlib import Path

def load_matlab_data(filepath):
    """Load and validate MATLAB data structure."""
    try:
        data = scipy.io.loadmat(filepath, squeeze_me=False)
        required_fields = ['spike_times', 'cursor_vel', 'time_frame', 
                          'trial_start_times', 'trial_end_times', 'trial_success']
        
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Required field '{field}' not found in MATLAB file")
        
        return data
    except Exception as e:
        print(f"Error loading MATLAB file: {e}")
        sys.exit(1)

def extract_spike_times(spike_times_cell):
    """Extract spike times from MATLAB cell array."""
    spike_times_cell = spike_times_cell.flatten()
    spike_times = []
    
    for cell in spike_times_cell:
        if cell.size > 0:
            spikes = cell.flatten()
            spike_times.append(spikes)
        else:
            spike_times.append(np.array([]))
    
    return spike_times

def bin_trial_data(spike_times, cursor_vel, time_frame, t_start, t_end, bin_size):
    """Bin spike and behavior data for a single trial."""
    # Create time bins
    bins = np.arange(t_start, t_end + bin_size, bin_size)
    bin_centers = bins[:-1] + bin_size/2
    
    if len(bins) < 2:
        return None, None, None  # Trial too short
    
    # Bin spikes for each unit
    n_units = len(spike_times)
    n_bins = len(bins) - 1
    spike_counts = np.zeros((n_bins, n_units))
    
    for i, unit_spikes in enumerate(spike_times):
        if len(unit_spikes) > 0:
            # Filter spikes within trial bounds
            trial_spikes = unit_spikes[(unit_spikes >= t_start) & (unit_spikes <= t_end)]
            if len(trial_spikes) > 0:
                counts, _ = np.histogram(trial_spikes, bins=bins)
                spike_counts[:, i] = counts
    
    # Interpolate behavior to bin centers
    # Ensure time_frame covers the trial period
    time_frame_flat = time_frame.flatten()
    cursor_vel_2d = cursor_vel.reshape(-1, 2)
    
    if t_start < time_frame_flat[0] or t_end > time_frame_flat[-1]:
        print(f"Warning: Trial time [{t_start:.3f}, {t_end:.3f}] outside time_frame bounds")
    
    behavior_binned = np.column_stack([
        np.interp(bin_centers, time_frame_flat, cursor_vel_2d[:, 0]),
        np.interp(bin_centers, time_frame_flat, cursor_vel_2d[:, 1])
    ])
    
    return spike_counts, behavior_binned, bin_centers

def quality_check_trial(spike_counts, behavior_data, bin_size):
    """Perform quality checks on trial data."""
    issues = []
    
    # Check firing rates (convert counts to Hz)
    firing_rates = spike_counts / bin_size
    max_firing_rate = np.max(firing_rates)
    if max_firing_rate > 200:
        issues.append(f"High firing rate: {max_firing_rate:.1f} Hz")
    
    # Check for NaN in behavior
    if np.any(np.isnan(behavior_data)):
        issues.append("NaN values in behavior data")
    
    return issues

def write_hdf5_trial(h5file, trial_idx, spike_counts, behavior_data, timestamps, quality_issues):
    """Write trial data to HDF5 file."""
    trial_group = h5file.create_group(f'trial_{trial_idx:04d}')
    
    # Store data arrays
    trial_group.create_dataset('spikes', data=spike_counts, compression='gzip')
    trial_group.create_dataset('behavior', data=behavior_data, compression='gzip')
    trial_group.create_dataset('timestamps', data=timestamps, compression='gzip')
    
    # Store metadata
    trial_group.attrs['n_bins'] = len(timestamps)
    trial_group.attrs['n_units'] = spike_counts.shape[1]
    trial_group.attrs['duration'] = timestamps[-1] - timestamps[0] if len(timestamps) > 1 else 0
    
    # Store quality issues
    if quality_issues:
        trial_group.attrs['quality_issues'] = '; '.join(quality_issues)
    else:
        trial_group.attrs['quality_issues'] = 'none'

def main():
    parser = argparse.ArgumentParser(description='Standardize neural spike and behavior data into HDF5 format')
    parser.add_argument('--input', required=True, help='Input MATLAB .mat file')
    parser.add_argument('--output', required=True, help='Output HDF5 .h5 file')
    parser.add_argument('--bin-size', type=float, default=0.02, help='Bin size in seconds (default: 0.02)')
    
    args = parser.parse_args()
    
    # Validate input file
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' does not exist")
        sys.exit(1)
    
    print(f"Loading data from {args.input}...")
    data = load_matlab_data(args.input)
    
    # Extract data arrays
    spike_times = extract_spike_times(data['spike_times'])
    cursor_vel = data['cursor_vel']
    time_frame = data['time_frame']
    trial_start_times = data['trial_start_times'].flatten()
    trial_end_times = data['trial_end_times'].flatten()
    trial_success = data['trial_success'].flatten().astype(bool)
    
    print(f"Found {len(spike_times)} units, {len(trial_start_times)} trials")
    print(f"Successful trials: {np.sum(trial_success)}")
    
    # Filter successful trials
    successful_indices = np.where(trial_success)[0]
    
    # Process trials and write HDF5
    with h5py.File(args.output, 'w') as h5file:
        # Store metadata
        h5file.attrs['bin_size'] = args.bin_size
        h5file.attrs['n_units'] = len(spike_times)
        h5file.attrs['n_successful_trials'] = len(successful_indices)
        h5file.attrs['source_file'] = args.input
        
        trials_written = 0
        trials_with_issues = 0
        
        for trial_idx in successful_indices:
            t_start = trial_start_times[trial_idx]
            t_end = trial_end_times[trial_idx]
            
            # Bin trial data
            spike_counts, behavior_data, timestamps = bin_trial_data(
                spike_times, cursor_vel, time_frame, t_start, t_end, args.bin_size
            )
            
            if spike_counts is None:
                print(f"Skipping trial {trial_idx}: too short")
                continue
            
            # Quality check
            quality_issues = quality_check_trial(spike_counts, behavior_data, args.bin_size)
            if quality_issues:
                trials_with_issues += 1
                print(f"Trial {trial_idx} quality issues: {'; '.join(quality_issues)}")
            
            # Write to HDF5
            write_hdf5_trial(h5file, trial_idx, spike_counts, behavior_data, timestamps, quality_issues)
            trials_written += 1
        
        h5file.attrs['trials_written'] = trials_written
        h5file.attrs['trials_with_quality_issues'] = trials_with_issues
    
    print(f"Successfully wrote {trials_written} trials to {args.output}")
    print(f"Trials with quality issues: {trials_with_issues}")

if __name__ == '__main__':
    main()
