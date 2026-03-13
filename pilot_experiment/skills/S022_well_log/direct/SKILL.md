# Borehole Well Log Resampling and Lithology Classification

## Overview
This skill enables resampling of irregularly-spaced borehole well log data to uniform depth intervals and classifies lithology using petrophysical crossplot rules based on gamma ray, resistivity, porosity, and density measurements.

## Workflow
1. Parse command line arguments for input CSV, output directory, and depth step interval
2. Load and validate well log data, checking for required columns and data quality
3. Calculate depth range and create uniform depth grid using specified step interval
4. Resample all log curves to uniform depth using linear interpolation
5. Compute derived petrophysical parameters (PHIT total porosity and Vsh shale volume)
6. Apply lithology classification rules using crossplot logic on multiple log parameters
7. Export resampled logs, lithology classifications, and generate summary statistics

## Common Pitfalls
- **Extrapolation beyond data range**: Linear interpolation fails outside original depth bounds - always clip resampled depth to min/max of input data
- **Division by zero in Vsh calculation**: When GR_max equals GR_min, handle by setting Vsh to 0 or using a small epsilon value
- **Missing or invalid log values**: NaN values in input data propagate through interpolation - implement data quality checks and gap handling
- **Incorrect units assumption**: Neutron porosity might be in percentage (0-100) instead of fraction (0-1) - validate reasonable ranges
- **Matrix density assumptions**: Using fixed 2.65 g/cm3 for sandstone matrix may not apply to carbonates - consider making this configurable

## Error Handling
- Validate input CSV contains all required columns before processing
- Check for sufficient data points (minimum 10) for reliable interpolation
- Handle NaN values by either interpolating across gaps or flagging problematic intervals
- Ensure output directory exists or create it, with proper file write permissions
- Implement bounds checking on calculated porosity and shale volume (clip to [0,1])

## Quick Reference
