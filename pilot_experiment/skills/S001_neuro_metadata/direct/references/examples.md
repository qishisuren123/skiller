# Example 1: Basic usage
python main.py /data/experiment_2023 -o experiment_meta.json

# Example 2: Processing mixed file types
"""
Directory structure:
/experiment/
  ├── session1/
  │   ├── spikes.h5      # HDF5 with /units/spike_times dataset
  │   └── behavior.mat   # MATLAB with trial_data variable
  └── session2/
      └── lfp.mat        # MATLAB v7.3 (HDF5 format)

Output meta.json:
{
  "scan_directory": "/experiment",
  "total_files": 3,
  "files": [
    {
      "path": "session1/spikes.h5",
      "file_type": "HDF5",
      "size_bytes": 1048576,
      "datasets": [
        {
          "path": "units/spike_times",
          "shape": [1000, 2],
          "dtype": "float64"
        }
      ]
    },
    {
      "path": "session1/behavior.mat",
      "file_type": "MATLAB", 
      "size_bytes": 524288,
      "variables": [
        {
          "name": "trial_data",
          "shape": [100, 5],
          "dtype": "float64"
        }
      ]
    }
  ]
}
"""
