# Example meta.json Output

Below is a representative `meta.json` output from scanning a neuroscience study directory containing EEG recordings for 50 subjects and a single shared stimulus file.

```json
{
  "summary": {
    "total_files": 51,
    "total_size_bytes": 4831838208,
    "total_size_human": "4.50 GB",
    "total_datasets": 206,
    "errors": 0,
    "format_breakdown": {
      "hdf5": 50,
      "mat": 1
    },
    "scan_duration_seconds": 12.47
  },
  "scan_config": {
    "root_dir": "/data/study/eeg-memory-task",
    "merge_enabled": true,
    "subject_pattern": "(?:sub|subject|subj|sbj|SUB)[-_]?\\d+",
    "shape_mode": "flexible",
    "large_file_threshold_bytes": 2147483648,
    "large_file_threshold_human": "2.00 GB"
  },
  "files": [
    {
      "file": "raw/sub-*_task-memory_eeg.h5",
      "size_bytes": 94371840,
      "size_human": "90.00 MB",
      "format": "hdf5",
      "datasets": [
        {
          "path": "eeg/raw",
          "shape": [15360, 64],
          "dtype": "float32",
          "nbytes": 3932160
        },
        {
          "path": "eeg/filtered",
          "shape": [15360, 64],
          "dtype": "float32",
          "nbytes": 3932160
        },
        {
          "path": "eeg/events",
          "shape": [48, 3],
          "dtype": "int64",
          "nbytes": 1152
        },
        {
          "path": "metadata/channels",
          "shape": [64],
          "dtype": "|S16",
          "nbytes": 1024
        }
      ],
      "error": null,
      "merged": true,
      "count": 50,
      "total_size_bytes": 4718592000,
      "total_size_human": "4.39 GB",
      "shape_dim0_ranges": {
        "eeg/raw": {
          "min": 14080,
          "max": 16640
        },
        "eeg/filtered": {
          "min": 14080,
          "max": 16640
        },
        "eeg/events": {
          "min": 44,
          "max": 52
        },
        "metadata/channels": {
          "min": 64,
          "max": 64
        }
      }
    },
    {
      "file": "stimuli/stimulus_params.mat",
      "size_bytes": 113246208,
      "size_human": "107.98 MB",
      "format": "mat",
      "datasets": [
        {
          "path": "image_paths",
          "shape": [200, 1],
          "dtype": "object",
          "nbytes": 1600
        },
        {
          "path": "onset_times",
          "shape": [200, 1],
          "dtype": "float64",
          "nbytes": 1600
        },
        {
          "path": "durations",
          "shape": [200, 1],
          "dtype": "float64",
          "nbytes": 1600
        },
        {
          "path": "conditions",
          "shape": [200, 1],
          "dtype": "uint8",
          "nbytes": 200
        }
      ],
      "error": null,
      "merged": false,
      "count": 1
    }
  ]
}
```

## Explanation of Key Sections

### `summary`

| Field | Description |
|-------|-------------|
| `total_files` | 51 files were discovered and inspected (50 subject HDF5 files + 1 MATLAB stimulus file). |
| `total_size_bytes` | Aggregate size across all files (~4.50 GB). |
| `total_datasets` | 206 total datasets: 50 files x 4 datasets each = 200, plus 4 datasets in the stimulus file, plus 2 metadata-only entries. |
| `errors` | No files failed to read. |
| `format_breakdown` | 50 files detected as HDF5, 1 as classic MATLAB. |
| `scan_duration_seconds` | The full scan took 12.47 seconds. |

### `scan_config`

Records the exact parameters used so the scan is reproducible. Notable: `shape_mode` is `"flexible"`, meaning dim-0 differences are ignored during merge signature comparison.

### `files` -- Merged Entry

The first entry in `files` is a **merged** group:

- `"file": "raw/sub-*_task-memory_eeg.h5"` -- The wildcard pattern replacing `sub-001` through `sub-050`.
- `"merged": true` -- Indicates this entry represents multiple files.
- `"count": 50` -- 50 individual files were merged into this entry.
- `"total_size_bytes"` / `"total_size_human"` -- Aggregate size across all 50 files.
- `"datasets"` -- Shows the structure from one representative file. The shapes shown are from the first file encountered.
- `"shape_dim0_ranges"` -- For each dataset, the minimum and maximum values of the first dimension across all 50 files. For example, `eeg/raw` has dim-0 ranging from 14,080 to 16,640 samples, reflecting different recording durations per subject. The `metadata/channels` dataset has a fixed dim-0 of 64 (same number of channels for all subjects).

### `files` -- Single (Non-Merged) Entry

The second entry is the stimulus parameters file:

- `"merged": false` -- This file was not merged with any others.
- `"count": 1` -- Only one file matches this path.
- No `"total_size_bytes"` or `"shape_dim0_ranges"` fields (these are only present on merged entries).
- `"format": "mat"` -- Read successfully with `scipy.io.loadmat` (classic MATLAB format).
