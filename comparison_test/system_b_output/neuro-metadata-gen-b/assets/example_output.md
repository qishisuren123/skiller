# Example Output

Running `python scripts/main.py test_data/ -o meta.json` on a dataset with 3
subjects and 2 additional MAT files produces:

```json
{
  "summary": {
    "total_files": 8,
    "total_size_bytes": 1949712,
    "total_size_human": "1.86 MB",
    "total_datasets": 94,
    "errors": 0,
    "format_counts": {
      "mat": 4,
      "hdf5": 3,
      "mat-v7.3-hdf5": 1
    },
    "scan_seconds": 0.04
  },
  "scan_config": {
    "root": "/data/neuroscience/zebrafish",
    "merge": true,
    "subject_regex": "(?:sub|subject|subj|sbj|SUB)[-_]?\\d+",
    "shape_compare": "flex"
  },
  "files": [
    {
      "path": "Additional_mat_files/CustomColormaps.mat",
      "format": "mat",
      "merged": false,
      "count": 1,
      "datasets": [
        {"key": "cluster_colors", "shape": [10, 3], "dtype": "float64"},
        {"key": "regression_colors", "shape": [6, 3], "dtype": "float64"}
      ]
    },
    {
      "path": "Subjects/subject_*/TimeSeries.h5",
      "format": "hdf5",
      "merged": true,
      "count": 3,
      "datasets": [
        {"key": "CellResp", "shape": [-1, 500], "dtype": "float32"},
        {"key": "CellRespAvr", "shape": [-1, 50], "dtype": "float32"},
        {"key": "CellRespAvrZ", "shape": [-1, 50], "dtype": "float32"},
        {"key": "CellRespZ", "shape": [-1, 500], "dtype": "float32"},
        {"key": "absIX", "shape": [-1, 1], "dtype": "int32"}
      ],
      "dim0_ranges": {
        "CellResp": {"min": 95, "max": 120},
        "absIX": {"min": 95, "max": 120}
      }
    }
  ]
}
```

The merged `TimeSeries.h5` entry shows that all 3 subjects share the same
5-dataset structure. The `dim0_ranges` field indicates that the neuron count
ranges from 95 to 120 across subjects. The `shape` field uses -1 for the
variable first dimension.
