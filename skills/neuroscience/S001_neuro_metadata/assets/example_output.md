{
  "files": [
    {
      "path": "/data/experiment_1/neural_data.h5",
      "type": "hdf5",
      "datasets": [
        {
          "name": "spikes/unit_001",
          "shape": [10000, 1],
          "dtype": "float64",
          "size_bytes": 80000
        },
        {
          "name": "lfp/channel_01",
          "shape": [50000, 1],
          "dtype": "float32",
          "size_bytes": 200000
        }
      ]
    },
    {
      "path": "/data/experiment_1/behavior.mat",
      "type": "matlab",
      "datasets": [
        {
          "name": "timestamps",
          "shape": [1000, 1],
          "dtype": "double"
        },
        {
          "name": "trial_data",
          "shape": [100, 5],
          "dtype": "double"
        }
      ]
    }
  ],
  "total_files": 2,
  "processing_errors": [],
  "error_count": 0
}
