# Example: meta.json output

Running the tool on a 3-subject zebrafish dataset produces:

```json
{
  "summary": {
    "total_files": 8,
    "total_size_bytes": 1949712,
    "total_size_human": "1.9 MB",
    "total_datasets": 94,
    "errors": 0,
    "format_counts": {"hdf5": 3, "mat": 4, "mat-v7.3-hdf5": 1}
  },
  "files": [
    {
      "path": "Subjects/subject_*/TimeSeries.h5",
      "format": "hdf5",
      "merged": true,
      "count": 3,
      "datasets": [
        {"key": "CellResp", "shape": [-1, 500], "dtype": "float32"},
        {"key": "CellRespAvr", "shape": [-1, 50], "dtype": "float32"}
      ]
    },
    {
      "path": "Additional_mat_files/CustomColormaps.mat",
      "format": "mat",
      "merged": false,
      "datasets": [
        {"key": "cluster_colors", "shape": [10, 3], "dtype": "float64"}
      ]
    }
  ]
}
```
