1. Load MATLAB .mat file using scipy.io.loadmat
2. Extract and reshape arrays using np.squeeze to handle MATLAB dimensions
3. Parse spike_times cell array by iterating over units and extracting with .flatten()
4. Filter trial indices where trial_success is True
5. For each successful trial:
   - Define trial time window from start/end times
   - Bin spike times using np.histogram with trial-specific time bins
   - Resample behavior data using scipy.interpolate.interp1d to match spike bins
   - Run quality checks for firing rates >200Hz and NaN behavior values
6. Save each trial as HDF5 group with spikes, behavior, timestamps datasets
7. Add quality flag as HDF5 attribute for each trial
8. Log processing statistics and save final file
