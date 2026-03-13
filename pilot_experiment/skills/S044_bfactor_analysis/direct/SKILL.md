# B-Factor Analysis Tool

## Overview
This skill helps create a command-line tool for analyzing B-factor (temperature factor) distributions in protein structures to identify flexible regions and assess structural reliability. B-factors indicate atomic displacement and are crucial for understanding protein dynamics and data quality.

## Workflow
1. **Parse command-line arguments** to extract B-factor data string and optional normalization flag
2. **Convert and validate B-factor data** from comma-separated string to numpy array with error checking
3. **Calculate comprehensive statistics** including mean, median, standard deviation, and quartiles using numpy/scipy
4. **Identify flexible regions** by finding residues above 75th percentile and group consecutive positions into segments
5. **Apply normalization** (if requested) using min-max scaling to 0-100 range
6. **Generate visualization** with matplotlib showing B-factor profile and highlighting flexible regions
7. **Export results** to structured JSON file containing all statistics, flexible regions, and normalized data

## Common Pitfalls
- **Invalid B-factor values**: Non-numeric or negative values in input data - validate and convert data types early with proper error messages
- **Empty flexible regions**: When no residues exceed 75th percentile threshold - handle edge case by reporting "No flexible regions identified"
- **Single-residue datasets**: Statistics become meaningless with insufficient data - require minimum dataset size (e.g., 5 residues)
- **Consecutive grouping logic**: Off-by-one errors when identifying segment boundaries - use proper indexing and test edge cases
- **File output permissions**: JSON/PNG files may fail to save due to directory permissions - implement try-catch with informative error messages

## Error Handling
- Validate input data format and convert to float array with descriptive error messages for parsing failures
- Check for minimum dataset size requirements before statistical analysis
- Handle file I/O exceptions when saving JSON results and PNG plots
- Implement graceful degradation when optional features (normalization, plotting) fail
- Provide clear error messages that guide users toward correct input format

## Quick Reference
