# Spike-Behavior Standardization — Expert Notes

## What You're Building
A script that reads neural spike + behavior data from a MATLAB file and writes a trial-based HDF5 file with binned spikes and resampled behavior.

## Key Steps
1. Load MAT file with `scipy.io.loadmat` — watch out, spike_times is a `(1, N_units)` object array
2. Filter by `trial_success` first, then loop over successful trials only
3. For each trial: bin spikes with `np.histogram(spike_times, bins)`, resample behavior with `np.interp`
4. Write HDF5 groups: `/trial_0000/spikes`, `/trial_0000/behavior`, `/trial_0000/timestamps`

## Pitfalls I've Learned the Hard Way
1. **Object array indexing**: `spike_times[0, unit]` not `spike_times[unit]`. The MATLAB cell array becomes a nested object array — flatten with `[0]`
2. **Bin edges vs centers**: `np.histogram` returns `n_bins+1` edges. Use `(edges[:-1] + edges[1:]) / 2` for bin centers
3. **Empty spikes**: Some units may have zero spikes in a trial. `np.histogram` handles this fine, returns zeros — don't special-case it
4. **Behavior resampling**: Use `np.interp(bin_centers, time_frame, vel)` — it extrapolates flat by default, which is fine for edge bins
5. **Quality flags**: Check `firing_rate = spike_count / bin_size`. Flag if > 200 Hz. Check `np.isnan(behavior).any()` per trial

## Reference
```python
bin_edges = np.arange(t_start, t_end + bin_size, bin_size)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
for u in range(n_units):
    spk = spike_times[0, u].flatten()
    trial_spk = spk[(spk >= t_start) & (spk < t_end)]
    counts, _ = np.histogram(trial_spk, bins=bin_edges)
    spike_matrix[:, u] = counts
behavior_resampled = np.column_stack([
    np.interp(bin_centers, time_frame, vel[:, 0]),
    np.interp(bin_centers, time_frame, vel[:, 1]),
])
```
