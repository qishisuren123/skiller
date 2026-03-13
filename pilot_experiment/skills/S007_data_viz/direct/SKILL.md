# Neural Population Activity Visualization

## Overview
This skill helps create publication-ready visualizations of neural population activity data from CSV files, generating heatmaps and population peristimulus time histograms (PSTHs) with proper statistical representations.

## Workflow
1. Parse command-line arguments for input CSV file and output directory paths
2. Load and validate CSV data structure (trial, time, neuron_* columns)
3. Reshape data into trials × time × neurons array for efficient computation
4. Calculate trial-averaged firing rates and population statistics (mean, SEM)
5. Generate firing rate heatmap showing neuron activity patterns across time
6. Create population PSTH with mean firing rate and standard error shading
7. Save both plots as PNG files and print data summary statistics

## Common Pitfalls
- **Missing neuron columns**: Always filter columns with `neuron_` prefix and handle cases where no neuron columns exist
- **Irregular time sampling**: Use `pivot_table` with aggregation to handle duplicate time points per trial
- **Memory issues with large datasets**: Process data in chunks or use memory-efficient pandas operations instead of loading entire arrays
- **Inconsistent trial/time combinations**: Validate that all trials have the same time points before reshaping
- **Empty output directory**: Create output directory if it doesn't exist using `os.makedirs(exist_ok=True)`

## Error Handling
- Validate CSV file exists and is readable before processing
- Check for required columns (trial, time) and at least one neuron column
- Handle missing values with appropriate interpolation or exclusion
- Catch matplotlib backend issues and ensure Agg backend is set before importing pyplot
- Provide informative error messages for malformed data structures

## Quick Reference
