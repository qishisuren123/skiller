# Well Log Data Resampling and Lithology Classification

## Overview
This skill helps create a Python CLI script for resampling borehole well log data to uniform depth intervals and classifying lithology based on petrophysical crossplot rules. It handles interpolation, data validation, porosity calculations, and generates structured outputs.

## Workflow
1. **Setup CLI arguments** - Use argparse for input file, output directory, and depth step parameters
2. **Read and validate data** - Load CSV, sort by depth, check data quality ranges
3. **Create uniform depth grid** - Generate new depth array within original bounds using specified step size
4. **Interpolate log curves** - Use scipy.interpolate.interp1d with proper bounds handling for all log parameters
5. **Calculate derived logs** - Compute PHIT (total porosity) and Vsh (shale volume) with realistic bounds
6. **Classify lithology** - Apply vectorized classification rules in proper priority order
7. **Generate outputs** - Save resampled logs, lithology classifications, and summary statistics

## Common Pitfalls
- **Interpolation bounds errors**: Use `bounds_error=False` with proper `fill_value` tuple for extrapolation
- **Depth grid generation**: Ensure new depths don't exceed original range by clipping final array
- **Unrealistic porosity values**: PHIT formula can produce negative/extreme values - always clip to [0, 0.5] range
- **Boolean Series ambiguity**: Don't use pandas apply() with complex boolean logic - use vectorized numpy operations instead
- **Classification rule conflicts**: Apply rules in priority order (limestone before sandstone) to avoid overlapping conditions
- **Constant gamma ray values**: Check for gr_max == gr_min to avoid division by zero in Vsh calculation

## Error Handling
- Sort input data by depth before interpolation
- Validate bulk density ranges and warn about porosity calculation issues
- Handle constant log values gracefully with appropriate warnings
- Use numpy boolean masks instead of pandas apply() for classification
- Clip all derived parameters to geologically realistic ranges

## Quick Reference
