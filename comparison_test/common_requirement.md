Generate a fine-grained metadata file (meta.json) for a neuroscience data folder. The tool should recursively scan a directory containing HDF5 (.h5) and MATLAB (.mat) files, extract the internal structure of each file (keys, shapes, dtypes, sizes), and produce a comprehensive JSON catalog.

## Dataset Context

The target dataset is a multi-subject neuroscience recording (e.g., Zebrafish Whole-Brain Sensorimotor Mapping). The data is organized hierarchically:

```
data_root/
  Additional_mat_files/
    CustomColormaps.mat       # RGB color palettes for visualization
    FishOutline.mat           # Spatial coordinates for anatomical overlay
  Subjects/
    subject_01/
      TimeSeries.h5           # Neural activity time series
      data_full.mat           # Metadata, anatomy, coordinates, behavior
    subject_02/
      TimeSeries.h5
      data_full.mat           # May be MATLAB v7.3 (HDF5-based)
    ...
```

## Key Technical Requirements

1. **HDF5 Inspection**: Recursively traverse nested groups and datasets in .h5 files. Record shape, dtype, and size for each dataset. Key datasets include:
   - CellResp (num_neurons x num_timepoints) — neural activity
   - CellRespAvr, CellRespAvrZ, CellRespZ — averaged/z-scored variants
   - absIX — absolute cell indices

2. **MATLAB .mat Reading**: Use scipy.io.loadmat for standard v5/v7 files. Key variables include:
   - periods, fpsec, numcell_full — experiment parameters
   - CellXYZ, CellXYZ_norm — spatial coordinates
   - anat_stack, anat_yx, anat_yz, anat_zx — anatomical imaging
   - timelists, timelists_names — stimulus timing
   - Behavior_raw, Behavior_full, BehaviorAvr — behavioral data
   - Eye_full, Eye_avr — eye tracking data

3. **MATLAB v7.3 Fallback**: Some .mat files are saved with -v7.3 flag (actually HDF5 internally). scipy.io.loadmat raises NotImplementedError or ValueError for these. Must auto-detect and fallback to h5py.

4. **Wildcard Pattern Merging**: When multiple subjects share the same file structure (e.g., all subject_*/TimeSeries.h5 have identical keys), merge them into a single entry with a wildcard pattern and record the count and dimension ranges.

5. **Output Format**: Generate meta.json with:
   - summary: total_files, total_size, format_counts, errors
   - files: per-file metadata with structure details
   - Merged entries should show matched_count and structure_consistent flag

6. **Error Handling**: Gracefully handle permission errors, corrupted files, and format mismatches. Log errors but continue processing remaining files.

The tool should be a standalone Python CLI script with argparse, supporting options like --output, --merge/--no-merge, --subject-pattern, and --shape-mode (exact/flexible/ndim_only).
