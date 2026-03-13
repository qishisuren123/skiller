# Neural Population Activity Visualization

## Overview
This skill helps create Python CLI scripts for visualizing neural population activity data from CSV files, generating heatmaps and population PSTH plots with proper error handling for missing data and performance optimization for large datasets.

## Workflow
1. **Set up imports and non-interactive backend** - Use matplotlib 'Agg' backend for server environments
2. **Load and identify neuron columns** - Extract columns starting with 'neuron_' prefix
3. **Create heatmap with smart labeling** - Use imshow with adaptive y-axis labels based on dataset size
4. **Calculate population PSTH with proper statistics** - Use pivot tables for correct SEM calculation across trials
5. **Handle missing data gracefully** - Use skipna=True and fillna() for NaN values
6. **Optimize for large datasets** - Use numpy operations and memory-efficient approaches

## Common Pitfalls
- **Seaborn dependency**: Remove seaborn to avoid import errors, use matplotlib's imshow instead
- **Heatmap axis labels**: Don't use grouped data index directly - extract values and create proper tick labels
- **DataFrame copy warnings**: Always use .copy() when modifying DataFrames to avoid SettingWithCopyWarning
- **Incorrect SEM calculation**: Use pivot_table to properly structure trials×time data for accurate statistics
- **NaN handling**: Missing neuron data breaks mean calculations - use skipna=True throughout
- **Label overcrowding**: Large datasets need adaptive y-axis labeling strategies
- **Memory issues**: Very large datasets may need fallback methods instead of pivot tables

## Error Handling
- **ModuleNotFoundError**: Remove optional dependencies like seaborn
- **SettingWithCopyWarning**: Create explicit DataFrame copies before modification
- **KeyError on calculated columns**: Ensure columns are added to proper DataFrame copy
- **TypeError with NaN operations**: Use skipna=True and fillna(0) for robust statistics
- **MemoryError**: Implement fallback groupby approach for datasets too large for pivot tables

## Quick Reference
