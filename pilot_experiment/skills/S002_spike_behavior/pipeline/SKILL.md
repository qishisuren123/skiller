# Neural Spike and Behavior Data Standardization to HDF5

## Overview
This skill helps create a robust Python CLI script to standardize neural spike and behavior data from MATLAB files into HDF5 format, handling common data quality issues, unit conversions, and edge cases that arise in neuroscience data processing.

## Workflow
1. **Setup argument parsing** with input/output files, bin size, and minimum duration parameters
2. **Load MATLAB data** and extract spike times, behavior data, and trial information
3. **Detect spike time units** (seconds vs milliseconds) using heuristic comparison with trial times
4. **Filter trials** by success status and minimum duration requirements
5. **Validate data coverage** ensuring behavior data spans the full trial duration
6. **Process each valid trial**:
   - Create time bins with proper edge handling
   - Bin spike data with unit conversion
   - Interpolate behavior data to match spike bins
   - Perform quality checks on firing rates and behavior data
7. **Save to HDF5** with sequential trial numbering and metadata attributes

## Common Pitfalls
- **Empty behavior data arrays**: Check for sufficient data points (≥2) before interpolation
- **Duplicate trial indices**: Use sequential numbering for HDF5 groups instead of original trial indices
- **Unit mismatches**: Spike times may be in milliseconds while trial times are in seconds - implement automatic detection
- **Extrapolation artifacts**: Validate that behavior data timeframe fully covers trial duration before processing
- **Very short trials**: Filter out trials below minimum duration threshold to ensure meaningful analysis
- **Firing rate calculation errors**: Use actual bin size (not nominal) when calculating rates from spike counts

## Error Handling
- **Interpolation errors**: Catch empty arrays and insufficient data points, skip problematic trials
- **HDF5 group conflicts**: Use sequential numbering and track original indices in attributes
- **Data validation**: Check trial duration, behavior data coverage, and spike data availability
- **Quality flagging**: Mark trials with high firing rates or NaN behavior data without failing
- **Graceful degradation**: Skip invalid trials while continuing to process valid ones

## Quick Reference
