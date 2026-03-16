INFO:__main__:Loading data from session_001.mat
INFO:__main__:Spike times shape: (1, 96)
INFO:__main__:Cursor velocity shape: (15420, 2)
INFO:__main__:Time frame shape: (15420,)
INFO:__main__:Number of units: 96
INFO:__main__:Found 847 successful trials out of 1203
INFO:__main__:Processed 847 trials, 23 flagged for quality issues
INFO:__main__:Data saved to standardized_data.h5

HDF5 file structure:
/trial_0000/
  ├── spikes (184, 96) - binned spike counts
  ├── behavior (184, 2) - resampled velocity  
  ├── timestamps (184,) - bin center times
  └── @flagged: False
/trial_0001/
  ├── spikes (133, 96)
  ├── behavior (133, 2)
  ├── timestamps (133,)
  └── @flagged: False
...
