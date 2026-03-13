---
name: spike-behavior-organize
description: "Standardize multi-format neural spike and behavior data (XDS .mat, PyalData .mat, NWB) into a unified trial-based HDF5 with structure /dataset/session/trial/{timestamps, spikes, behavior}. Handles MATLAB struct unpacking, NWB VectorIndex spike extraction, time resampling, and kinematics unification. Use this skill when the user needs to merge neural recordings from different labs or formats into a standardized file."
license: MIT
compatibility: "Python >=3.9; h5py >=3.9.0; scipy >=1.11.0; numpy >=1.24.0; pynwb >=2.5.0; pandas >=2.0.0."
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Multi-Format Neural Spike and Behavior Data Organizer

Reads neural spike and behavior data from four different source formats (XDS
MATLAB structs, PyalData trial arrays, and two NWB datasets), standardizes
them into a unified trial-based HDF5 file with consistent binning, spike
counts, and kinematics (position, velocity, acceleration).

## When to Use This Skill

- "Merge neural recordings from different labs into one standardized file"
- "Convert XDS and NWB data into a unified HDF5 for training"
- "Standardize spike and behavior data across multiple formats"
- "Unify trial-based neural data with consistent time binning"
- "I have Dryad + DANDI datasets, organize them together"

## Inputs

- **config_file** (required): JSON config specifying datasets, sessions, file paths
- **--bin-size**: Target bin size in seconds (default: 0.02 = 20ms)
- **--output**: Output HDF5 file path
- **--no-quality-check**: Skip quality checking step

## Workflow

1. **Load**: Read raw data using format-specific loaders (`scripts/main.py`)
2. **Filter**: Keep only successful trials using per-format outcome mapping
3. **Bin spikes**: Convert spike times to bin counts via `np.histogram`
4. **Resample behavior**: Interpolate behavior data to uniform bin centers
5. **Unify kinematics**: Compute position/velocity/acceleration triple
6. **Quality check**: Flag problematic trials with bitmask quality flags
7. **Write HDF5**: Output standardized `/dataset/session/trial/` structure

Run `scripts/main.py --help` for full CLI options. See `references/workflow.md` for details.

## Error Handling

Common errors and how to handle them:

1. **`KeyError` / `IndexError` on MATLAB struct**: XDS structs are wrapped in `(1,1)` numpy arrays. Handle by unwrapping with `[0,0]` or `.flat[0]` before field access.
2. **NWB `VectorIndex` exception**: Do not access `units['spike_times']` directly. Handle by using `units.get_unit_spike_times(idx)` to iterate per unit.
3. **In-place modification error**: `behavior_raw` must not be modified in the trial loop. Troubleshoot by creating a fresh `trial_behavior` dict per trial to avoid data corruption.
4. **Resampling `ValueError`**: When target bin size is not an integer multiple of original bin size for PyalData. Handle by choosing a compatible bin size or using interpolation fallback.

## Common Pitfalls

1. **MATLAB struct `[0,0]` unpacking**: `scipy.io.loadmat` wraps structs in `(1,1)` shaped arrays; must index with `[0,0]`.
2. **NWB spike extraction**: Use `units.get_unit_spike_times(idx)`, not dictionary access on the Units table.
3. **Behavior data in-place corruption**: Never overwrite `behavior_raw` inside the trial loop; use a copy per trial.

See `references/pitfalls.md` for the full list with tracebacks and fixes.

## Output Format

```
/dataset_name/
  session_name/
    trial_0000/
      timestamps    (N_bins,)       float64
      spikes        (N_bins, N_units) int32
      behavior/
        position      (N_bins, D)   float64
        velocity      (N_bins, D)   float64
        acceleration  (N_bins, D)   float64
```

See `assets/example_output.md` for a complete example with metadata attributes.
