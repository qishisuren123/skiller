---
name: spike_behavior
description: "Write a Python CLI script that standardizes neural spike and behavior data into a unified trial-based HDF5 file.

Input: A MATLAB .mat file containing:
- spike_times: a (1, N_units) cell array where each cell contains spike timestamps for one unit
- cursor_vel: velocity data array (T, 2) with x,y components  
- time_frame: timestamps for behavior data (T,)
- trial_start_times, trial_end_times: trial boundary timestamps
- trial_success: boolean array indicating successful trials

Output: HDF5 file with trial groups containing binned spikes, resampled behavior, timestamps, and quality flags."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: neuroscience
---

# Spike Behavior

## Overview
This skill creates a Python CLI script that standardizes neural spike and behavior data from MATLAB .mat files into a unified trial-based HDF5 format. The script handles MATLAB cell arrays, bins spike data, resamples behavior data to match spike timing, performs quality checks, and filters for successful trials only.

## When to Use
- Converting MATLAB neural data to standardized HDF5 format
- Preprocessing spike and behavior data for analysis pipelines
- Creating trial-aligned datasets from continuous recordings
- Quality control and flagging of neural data trials

## Inputs
- MATLAB .mat file containing spike times (cell array), cursor velocity, timestamps, trial boundaries, and success flags
- Bin size for spike binning (default 20ms)
- Output HDF5 filename

## Workflow
1. Load and parse MATLAB data using scripts/main.py
2. Extract spike times from cell arrays and handle MATLAB array dimensions
3. Filter for successful trials only
4. For each trial: bin spikes, resample behavior data, perform quality checks
5. Save trial data to HDF5 groups with metadata
6. Reference references/pitfalls.md for common MATLAB loading issues

## Error Handling
The script includes comprehensive error handling for MATLAB data loading issues. It handles cell array extraction errors, dimension mismatches, and interpolation failures. Quality checks flag trials with excessive firing rates or NaN behavior values, allowing downstream analysis to handle problematic data appropriately.

## Common Pitfalls
- MATLAB cell arrays require special handling with scipy.io.loadmat
- Array dimensions need squeezing to remove singleton dimensions
- Boolean logic in quality checks must use explicit Python bool conversion
- Interpolation can fail with insufficient data points

## Output Format
HDF5 file with trial groups (trial_XXXX) containing:
- spikes: binned spike counts (time_bins, units)
- behavior: resampled velocity (time_bins, 2) 
- timestamps: bin center times
- flagged: boolean quality flag attribute
