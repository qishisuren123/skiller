# Example HDF5 Output Structure

This document shows the complete structure of a standardized HDF5 file
produced by the spike-behavior-organize pipeline, including dataset shapes,
dtypes, and metadata attributes.

---

## File: `standardized_output.h5`

```
standardized_output.h5                          (HDF5 file)
│
│   attrs:
│       bin_size_s          = 0.02              (float64)
│       created_by          = "spike_behavior_organize"
│       config              = "{...}"           (JSON string of full config)
│
├── monkey_C/                                   (dataset group)
│   │
│   ├── session_20230101/                       (session group, XDS source)
│   │   │   attrs:
│   │   │       n_trials    = 142
│   │   │
│   │   ├── trial_0000/
│   │   │   │   attrs:
│   │   │   │       duration_s  = 1.56          (float64)
│   │   │   │       n_bins      = 78            (int)
│   │   │   │       n_units     = 96            (int)
│   │   │   │       qc_flags    = 0             (int, 0 = all checks passed)
│   │   │   │
│   │   │   ├── timestamps                     (78,)           float64  gzip
│   │   │   │       [0.01, 0.03, 0.05, ..., 1.55]
│   │   │   │
│   │   │   ├── spikes                         (78, 96)        int32    gzip
│   │   │   │       [[0, 1, 0, ..., 2],
│   │   │   │        [1, 0, 0, ..., 0],
│   │   │   │        ...]
│   │   │   │
│   │   │   └── behavior/
│   │   │       ├── position                   (78, 2)         float64  gzip
│   │   │       │       attrs: shape = [78, 2]
│   │   │       │       [[-12.3, 5.1], [-12.1, 5.3], ...]
│   │   │       │
│   │   │       ├── velocity                   (78, 2)         float64  gzip
│   │   │       │       attrs: shape = [78, 2]
│   │   │       │       [[8.2, -3.1], [8.5, -2.9], ...]
│   │   │       │
│   │   │       ├── acceleration               (78, 2)         float64  gzip
│   │   │       │       attrs: shape = [78, 2]
│   │   │       │       [[15.0, 10.0], [14.8, 9.5], ...]
│   │   │       │
│   │   │       └── emg                        (78, 12)        float64  gzip
│   │   │               attrs: shape = [78, 12]
│   │   │               [[0.12, 0.05, ..., 0.08], ...]
│   │   │
│   │   ├── trial_0001/
│   │   │   │   attrs:
│   │   │   │       duration_s  = 2.34
│   │   │   │       n_bins      = 117
│   │   │   │       n_units     = 96
│   │   │   │       qc_flags    = 1
│   │   │   │       qc_issues   = "EMPTY_UNITS"
│   │   │   │
│   │   │   ├── timestamps                     (117,)          float64  gzip
│   │   │   ├── spikes                         (117, 96)       int32    gzip
│   │   │   └── behavior/
│   │   │       ├── position                   (117, 2)        float64  gzip
│   │   │       ├── velocity                   (117, 2)        float64  gzip
│   │   │       └── acceleration               (117, 2)        float64  gzip
│   │   │
│   │   ├── trial_0002/
│   │   │       ...
│   │   └── ...
│   │       (up to trial_0141)
│   │
│   └── session_20230315/                       (session group, NWB source)
│       │   attrs:
│       │       n_trials    = 87
│       │
│       ├── trial_0000/
│       │   │   attrs:
│       │   │       duration_s  = 3.12
│       │   │       n_bins      = 156
│       │   │       n_units     = 128
│       │   │       qc_flags    = 0
│       │   │
│       │   ├── timestamps                     (156,)          float64  gzip
│       │   ├── spikes                         (156, 128)      int32    gzip
│       │   └── behavior/
│       │       ├── position                   (156, 3)        float64  gzip
│       │       │       attrs: shape = [156, 3]
│       │       ├── velocity                   (156, 3)        float64  gzip
│       │       │       attrs: shape = [156, 3]
│       │       └── acceleration               (156, 3)        float64  gzip
│       │               attrs: shape = [156, 3]
│       │
│       └── ...
│
└── monkey_M/                                   (second dataset group)
    │
    └── session_20230210/                       (session group, PyalData source)
        │   attrs:
        │       n_trials    = 203
        │
        ├── trial_0000/
        │   │   attrs:
        │   │       duration_s  = 1.08
        │   │       n_bins      = 54
        │   │       n_units     = 192           (M1: 96 + PMd: 96, merged)
        │   │       qc_flags    = 0
        │   │
        │   ├── timestamps                     (54,)           float64  gzip
        │   ├── spikes                         (54, 192)       int32    gzip
        │   └── behavior/
        │       ├── position                   (54, 2)         float64  gzip
        │       ├── velocity                   (54, 2)         float64  gzip
        │       └── acceleration               (54, 2)         float64  gzip
        │
        └── ...
```

---

## Attribute Summary

### Root-level attributes

| Attribute     | Type    | Description                                |
|---------------|---------|--------------------------------------------|
| `bin_size_s`  | float64 | Bin width in seconds (e.g., 0.02)          |
| `created_by`  | string  | Pipeline identifier                        |
| `config`      | string  | Full JSON config used for this run         |

### Session-level attributes

| Attribute   | Type | Description                        |
|-------------|------|------------------------------------|
| `n_trials`  | int  | Number of trials in this session   |

### Trial-level attributes

| Attribute     | Type   | Description                                          |
|---------------|--------|------------------------------------------------------|
| `duration_s`  | float  | Trial duration in seconds                            |
| `n_bins`      | int    | Number of time bins                                  |
| `n_units`     | int    | Number of neural units (columns in spikes)           |
| `qc_flags`    | int    | Bitmask of quality-check flags (0 = passed)          |
| `qc_issues`   | string | Comma-separated flag names (only present if qc != 0) |

### Behavior dataset attributes

| Attribute | Type       | Description                    |
|-----------|------------|--------------------------------|
| `shape`   | list[int]  | Shape of the dataset           |

---

## Quality Check Flag Reference

| Flag                 | Bit | Value | Meaning                                  |
|----------------------|-----|-------|------------------------------------------|
| `EMPTY_UNITS`        | 0   | 1     | Some units fired zero spikes             |
| `HIGH_FR`            | 1   | 2     | Unit firing rate exceeded 300 Hz         |
| `NAN_BEHAVIOR`       | 2   | 4     | NaN values in behavior data              |
| `SHORT_TRIAL`        | 3   | 8     | Trial shorter than minimum duration      |
| `LOW_SPIKE_COUNT`    | 4   | 16    | Suspiciously few total spikes            |
| `CONSTANT_BEHAVIOR`  | 5   | 32    | A behavior channel has zero variance     |

Example: `qc_flags = 5` means `EMPTY_UNITS` (1) + `NAN_BEHAVIOR` (4).

---

## Typical File Sizes

| Scenario                              | Approx. Size |
|---------------------------------------|-------------|
| 1 session, 100 trials, 96 units       | 15-25 MB    |
| 1 session, 200 trials, 192 units      | 50-80 MB    |
| 5 sessions, mixed formats, ~500 trials | 100-200 MB  |

Sizes are with gzip level 4 compression.  Uncompressed data would be roughly
3-5x larger.
