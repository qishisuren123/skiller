# Spike-Behavior-Organize: 7-Step Workflow

## Overview

This document describes the complete pipeline for standardizing multi-format
neural spike and behavior data into a unified HDF5 file.  The pipeline handles
three input formats (XDS `.mat`, NWB `.nwb`, PyalData `.mat`) and produces a
single output schema regardless of source.

---

## Step 1: Data Loading (Per-Format)

Each input format has a dedicated loader that extracts the raw data into a
common intermediate representation.

### XDS `.mat` files
- Use `scipy.io.loadmat` with `squeeze_me=False, struct_as_record=True`.
- Unwrap the MATLAB struct via `[0, 0]` indexing on the structured array.
- Discover fields using `dtype.names`.
- Extract `spike_times` from the cell array (object array of 1-D float arrays).
- Extract continuous signals: `cursor_vel`, `cursor_pos`, `EMG`, `time_frame`.
- Build `trial_info_table` as a `pd.DataFrame` from the nested trial struct.

### NWB files
- Open with `pynwb.NWBHDF5IO` in read mode with `load_namespaces=True`.
- Extract spike times by iterating `units.get_unit_spike_times(idx)` for each
  unit in the units table.
- Search for behavior timeseries in `processing['behavior']` first, then fall
  back to `acquisition`.  Handle both `TimeSeries` and `SpatialSeries` inside
  `Position` containers.
- Extract the trials table via `nwbfile.trials.to_dataframe()`.

### PyalData `.mat` files
- Load the struct array, handling both `(N_trials, 1)` and `(1, N_trials)` shapes.
- Auto-detect spike fields by matching field names against `*spikes*`.
- Merge multi-brain-area spike matrices (e.g., `M1_spikes`, `PMd_spikes`) via
  `np.hstack` along the unit axis.
- Auto-detect `bin_size` from the data field if present.

**Key output:** A dict containing spike times (or binned counts), behavior
signals with timestamps, and trial metadata.

---

## Step 2: Trial Filtering

Filter trials to keep only successful / valid ones using the `SUCCESS_MARKERS`
dictionary, which maps each source type to its outcome field and success value:

| Source Type   | Field     | Success Value | Notes                        |
|---------------|-----------|---------------|------------------------------|
| `xds`         | `result`  | `"R"`         | MATLAB char, may be bytes    |
| `pyaldata`    | `result`  | `1`           | Numeric flag                 |
| `nwb_000121`  | `outcome` | `"success"`   | String in trials table       |
| `nwb_000070`  | (none)    | (none)        | No outcome field; keep all   |

Additionally, apply a minimum-duration filter (default 0.1 s) using
`start_time` / `end_time` columns (auto-detected from several naming
conventions).

Byte-string values from MATLAB are decoded to UTF-8 and stripped before
comparison.

---

## Step 3: Spike Binning

Convert spike times to binned spike counts on a uniform time grid.

1. **Create uniform bins:** `np.arange(t_start, t_end + bin_size/2, bin_size)`
   produces bin edges; bin centers are the midpoints.
2. **Histogram per unit:** For each unit, `np.histogram(spike_times, bins=bin_edges)`
   yields a count vector.  Stack into `(N_bins, N_units)` int32 array.
3. **For PyalData:** Spikes are already binned.  If the target bin size differs
   from the original, use `resample_already_binned` which supports:
   - Integer-ratio summation (exact, preferred).
   - Interpolation with count scaling (fallback for non-integer ratios).

---

## Step 4: Behavior Resampling

Align behavior signals to the same uniform time bins as the spikes.

- **Continuous signals (XDS, NWB):** Use `scipy.interpolate.interp1d` with
  `kind='linear'` and `fill_value='extrapolate'`.  Each dimension is
  interpolated independently.
- **Already-binned signals (PyalData):** Use `resample_already_binned` (same
  logic as spike rebinning but for float data).
- **Time slicing:** For per-trial processing, slice behavior to the trial
  window (with one bin of margin on each side) before interpolation to avoid
  edge artifacts.

---

## Step 5: Kinematics Unification

Convert whatever kinematic representation is available into a full set of
`{position, velocity, acceleration}`.

### Conversion logic (`compute_kinematics`)
- **From position:** velocity = `np.gradient(pos, dt)`, acceleration = `np.gradient(vel, dt)`.
- **From velocity:** position = `np.cumsum(vel) * dt`, acceleration = `np.gradient(vel, dt)`.
- **From acceleration:** velocity = `np.cumsum(acc) * dt`, position = `np.cumsum(vel) * dt`.

A Gaussian smoothing kernel (`gaussian_filter1d`, sigma in bins) is applied
before differentiation to suppress high-frequency noise.

### Source-type routing (`unify_behavior`)
- **XDS:** Prefer `cursor_vel` (velocity), fall back to `cursor_pos` (position).
  Preserve `emg` as-is.
- **NWB:** Search for known velocity keys, then position keys, then take
  whatever is available.
- **PyalData:** Search for `vel` / `hand_vel` / `cursor_vel`, then positional
  equivalents.

---

## Step 6: Quality Checking

Run `quality_check_trial` on each processed trial.  Returns a bitmask of flags:

| Flag                   | Bit | Condition                                   |
|------------------------|-----|---------------------------------------------|
| `EMPTY_UNITS`          | 0   | Any unit has zero spikes in the trial        |
| `HIGH_FR`              | 1   | Any unit exceeds 300 Hz mean firing rate     |
| `NAN_BEHAVIOR`         | 2   | Any NaN values in behavior arrays            |
| `SHORT_TRIAL`          | 3   | Trial duration < `min_duration_s`            |
| `LOW_SPIKE_COUNT`      | 4   | Total spike count < `min_total_spikes`       |
| `CONSTANT_BEHAVIOR`    | 5   | Any behavior channel has near-zero variance  |

Flags are stored as an integer attribute on each trial group in the output
HDF5, along with a human-readable comma-separated string of active issues.

This step can be skipped via `--no-quality-check` for faster processing.

---

## Step 7: HDF5 Output

Write the standardized data to a single HDF5 file with gzip compression.

### Schema

```
/
  attrs: bin_size_s, created_by, config
  /<dataset_name>/
    /<session_name>/
      attrs: n_trials
      /trial_0000/
        attrs: duration_s, n_bins, n_units, qc_flags, [qc_issues]
        timestamps     (N_bins,)          float64, gzip
        spikes         (N_bins, N_units)  int32,   gzip
        behavior/
          position       (N_bins, D)      float64, gzip
          velocity       (N_bins, D)      float64, gzip
          acceleration   (N_bins, D)      float64, gzip
          [emg]          (N_bins, N_mus)  float64, gzip  (optional)
      /trial_0001/
        ...
```

### Verification

After writing, `verify_hdf5` reads back the file, walks all groups and
datasets, logs shapes and dtypes, and checks for unexpected NaN values.

---

## Running the Pipeline

### Config file format (JSON)

```json
{
  "bin_size_s": 0.02,
  "output_path": "standardized_output.h5",
  "quality_check": true,
  "datasets": [
    {
      "name": "monkey_C",
      "sessions": [
        {
          "name": "session_20230101",
          "filepath": "/data/monkey_C/session1.mat",
          "format": "xds",
          "source_type": "xds"
        },
        {
          "name": "session_20230102",
          "filepath": "/data/monkey_C/session2.nwb",
          "format": "nwb",
          "source_type": "nwb_000121"
        }
      ]
    }
  ]
}
```

### CLI usage

```bash
python main.py config.json
python main.py config.json --bin-size 0.01 --output custom_output.h5
python main.py config.json --no-quality-check
```
