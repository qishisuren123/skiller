import argparse
import numpy as np
import h5py
import scipy.io
from scipy.interpolate import interp1d
import logging

def load_mat_data(input_file):
    """Load data from MATLAB .mat file"""
    data = scipy.io.loadmat(input_file)
    
    # Handle MATLAB arrays properly - squeeze to remove singleton dimensions
    time_frame = np.squeeze(data['time_frame'])
    cursor_vel = np.squeeze(data['cursor_vel'])
    
    # Ensure time_frame is 1D
    if time_frame.ndim == 0:
        time_frame = np.array([time_frame])
    
    # Ensure cursor_vel is 2D (T, 2)
    if cursor_vel.ndim == 1:
        cursor_vel = cursor_vel.reshape(-1, 1)
    
    return {
        'spike_times': data['spike_times'],
        'cursor_vel': cursor_vel,
        'time_frame': time_frame,
        'trial_start_times': np.squeeze(data['trial_start_times']),
        'trial_end_times': np.squeeze(data['trial_end_times']),
        'trial_success': np.squeeze(data['trial_success']).astype(bool)
    }

def bin_spikes(spike_times_cell, trial_start, trial_end, bin_size):
    """Bin spike times for a single trial"""
    trial_duration = trial_end - trial_start
    n_bins = int(np.ceil(trial_duration / bin_size))
    bin_edges = np.linspace(trial_start, trial_start + n_bins * bin_size, n_bins + 1)
    
    binned_spikes = []
    
    # Handle MATLAB cell array - extract each unit's spike times
    for i in range(spike_times_cell.shape[1]):  # Iterate over units
        unit_spikes = spike_times_cell[0, i].flatten()  # Extract from cell
        
        # Filter spikes within trial window
        trial_spikes = unit_spikes[(unit_spikes >= trial_start) & (unit_spikes <= trial_end)]
        counts, _ = np.histogram(trial_spikes, bins=bin_edges)
        binned_spikes.append(counts)
    
    bin_centers = bin_edges[:-1] + bin_size/2
    return np.array(binned_spikes).T, bin_centers

def resample_behavior(cursor_vel, time_frame, bin_centers):
    """Resample behavior data to match spike bin centers"""
    # Ensure we have enough data points for interpolation
    if len(time_frame) < 2 or len(cursor_vel) < 2:
        # Return NaN array if insufficient data
        return np.full((len(bin_centers), 2), np.nan)
    
    interp_x = interp1d(time_frame, cursor_vel[:, 0], kind='linear', 
                       bounds_error=False, fill_value=np.nan)
    interp_y = interp1d(time_frame, cursor_vel[:, 1], kind='linear',
                       bounds_error=False, fill_value=np.nan)
    
    resampled_vel = np.column_stack([interp_x(bin_centers), interp_y(bin_centers)])
    return resampled_vel

def quality_check(binned_spikes, behavior, bin_size):
    """Check data quality - flag high firing rates and NaN behavior"""
    # Check firing rates (convert from counts to Hz)
    firing_rates = binned_spikes / bin_size
    max_firing_rate = np.max(firing_rates) if firing_rates.size > 0 else 0
    high_fr_flag = bool(np.any(firing_rates > 200))
    
    # Check for NaN in behavior - be more explicit
    has_nan = np.isnan(behavior)
    nan_count = np.sum(has_nan)
    nan_behavior_flag = bool(nan_count > 0)
    
    return high_fr_flag or nan_behavior_flag

def main():
    parser = argparse.ArgumentParser(description='Standardize neural spike and behavior data')
    parser.add_argument('--input', required=True, help='Input .mat file')
    parser.add_argument('--output', required=True, help='Output .h5 file')
    parser.add_argument('--bin-size', type=float, default=0.02, help='Bin size in seconds')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load data
    logger.info(f"Loading data from {args.input}")
    data = load_mat_data(args.input)
    
    # Debug: check data shapes and ranges
    logger.info(f"Spike times shape: {data['spike_times'].shape}")
    logger.info(f"Cursor velocity shape: {data['cursor_vel'].shape}")
    logger.info(f"Time frame shape: {data['time_frame'].shape}")
    logger.info(f"Number of units: {data['spike_times'].shape[1]}")
    
    # Filter successful trials
    successful_trials = np.where(data['trial_success'])[0]
    logger.info(f"Found {len(successful_trials)} successful trials out of {len(data['trial_success'])}")
    
    # Create HDF5 file
    with h5py.File(args.output, 'w') as h5f:
        flagged_trials = 0
        
        for i, trial_idx in enumerate(successful_trials):
            trial_start = data['trial_start_times'][trial_idx]
            trial_end = data['trial_end_times'][trial_idx]
            
            # Bin spikes
            binned_spikes, bin_centers = bin_spikes(data['spike_times'], trial_start, trial_end, args.bin_size)
            
            # Resample behavior
            resampled_behavior = resample_behavior(data['cursor_vel'], data['time_frame'], bin_centers)
            
            # Quality check
            is_flagged = quality_check(binned_spikes, resampled_behavior, args.bin_size)
            if is_flagged:
                flagged_trials += 1
                logger.warning(f"Trial {trial_idx:04d} flagged for quality issues")
            
            # Save to HDF5
            trial_group = h5f.create_group(f'trial_{trial_idx:04d}')
            trial_group.create_dataset('spikes', data=binned_spikes)
            trial_group.create_dataset('behavior', data=resampled_behavior)
            trial_group.create_dataset('timestamps', data=bin_centers)
            trial_group.attrs['flagged'] = is_flagged
        
        logger.info(f"Processed {len(successful_trials)} trials, {flagged_trials} flagged for quality issues")
        logger.info(f"Data saved to {args.output}")

if __name__ == '__main__':
    main()
