# Example 1: Basic trial processing workflow
import numpy as np
import h5py

# Simulate MATLAB-like data
spike_times = [np.array([0.1, 0.3, 0.7]), np.array([0.2, 0.5])]  # 2 units
time_frame = np.linspace(0, 1, 1000)
cursor_vel = np.random.randn(1000, 2)
t_start, t_end = 0.0, 1.0
bin_size = 0.1

# Create bins and bin centers
bins = np.arange(t_start, t_end + bin_size, bin_size)
bin_centers = bins[:-1] + bin_size/2

# Bin spikes
spike_counts = np.zeros((len(bins)-1, len(spike_times)))
for i, unit_spikes in enumerate(spike_times):
    counts, _ = np.histogram(unit_spikes, bins=bins)
    spike_counts[:, i] = counts

# Interpolate behavior
behavior_binned = np.column_stack([
    np.interp(bin_centers, time_frame, cursor_vel[:, 0]),
    np.interp(bin_centers, time_frame, cursor_vel[:, 1])
])

print(f"Spike counts shape: {spike_counts.shape}")  # (10, 2)
print(f"Behavior shape: {behavior_binned.shape}")   # (10, 2)

# Example 2: HDF5 structure creation with quality checks
with h5py.File('neural_data.h5', 'w') as f:
    # Global metadata
    f.attrs['bin_size'] = 0.02
    f.attrs['n_units'] = 96
    
    # Trial data with quality assessment
    trial_group = f.create_group('trial_0001')
    
    # Simulate trial data
    n_bins, n_units = 50, 96
    spikes = np.random.poisson(2, (n_bins, n_units))  # Poisson spike counts
    behavior = np.random.randn(n_bins, 2) * 10  # Velocity data
    timestamps = np.arange(n_bins) * 0.02
    
    # Quality checks
    firing_rates = spikes / 0.02  # Convert to Hz
    max_rate = np.max(firing_rates)
    has_nan = np.any(np.isnan(behavior))
    
    issues = []
    if max_rate > 200:
        issues.append(f"High firing rate: {max_rate:.1f} Hz")
    if has_nan:
        issues.append("NaN in behavior")
    
    # Store data and metadata
    trial_group.create_dataset('spikes', data=spikes, compression='gzip')
    trial_group.create_dataset('behavior', data=behavior, compression='gzip')
    trial_group.create_dataset('timestamps', data=timestamps, compression='gzip')
    trial_group.attrs['quality_issues'] = '; '.join(issues) if issues else 'none'
    
    print(f"Trial quality: {trial_group.attrs['quality_issues']}")
