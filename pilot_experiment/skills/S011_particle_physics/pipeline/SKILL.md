# Particle Physics Data Analysis CLI Script

## Overview
This skill helps create a robust Python CLI script for analyzing particle physics collision data, including data loading, cleaning, quality cuts, signal/background classification, and statistical analysis with proper memory optimization and error handling.

## Workflow
1. **Setup argument parsing** with required input/output paths and optional mass window
2. **Load and validate data** with proper column checking and memory-efficient data types
3. **Clean data** by removing NaN values and physically invalid entries
4. **Apply quality cuts sequentially** while tracking cut flow statistics
5. **Classify events** as signal or background based on mass window and lepton criteria
6. **Calculate statistics** including significance and signal-to-noise ratio
7. **Save results** as filtered CSV and summary JSON with cut flow information

## Common Pitfalls
- **Mass window parsing**: Always validate format and logical consistency (min < max, positive values)
- **Boolean mask operations**: Use `.map()` incorrectly on boolean masks - instead set default values and use `.loc[]` for assignment
- **Division by zero**: Check for zero denominators in significance and SNR calculations
- **Memory issues**: Avoid creating unnecessary DataFrame copies; use boolean masks and proper data types
- **Cut flow tracking**: Track each cut individually rather than applying all at once
- **NaN handling**: Check for required columns and clean data before analysis

## Error Handling
- Validate input file exists and has required columns
- Handle empty datasets at each processing stage
- Gracefully handle division by zero in statistical calculations
- Provide informative error messages for invalid mass window formats
- Check for sufficient events after each filtering step
- Handle memory constraints with optimized data types and operations

## Quick Reference
