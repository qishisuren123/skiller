# Grain Size Distribution Analysis

## Overview
This skill enables analysis of grain size measurements from materials science image analysis, computing statistical distributions and classification metrics commonly used in materials characterization and metallography.

## Workflow
1. **Parse Input Data**: Extract grain diameter measurements from command line arguments and convert to numerical arrays for statistical analysis
2. **Compute Basic Statistics**: Calculate fundamental statistical measures (mean, median, std dev, min, max) for the grain size dataset
3. **Calculate Distribution Percentiles**: Determine D10, D30, D50, D60, D90 percentiles and derive uniformity coefficients (Cu, Cc) for grain distribution characterization
4. **Classify Grain Sizes**: Categorize grains into standard materials science size classes (Fine <50μm, Medium 50-200μm, Coarse >200μm) with count and percentage analysis
5. **Generate Histogram Visualization**: Create publication-quality histogram with appropriate binning strategy and materials science formatting conventions
6. **Export Results**: Structure and save comprehensive analysis results to JSON format with clear sectioning for downstream materials characterization workflows

## Common Pitfalls
- **Inadequate Bin Selection**: Using default matplotlib bins can obscure important grain size distributions. Solution: Use Freedman-Diaconis rule or materials-specific bin widths (e.g., 10-20 μm bins)
- **Percentile Calculation Errors**: Using wrong interpolation method for percentiles can affect D-values critical for materials classification. Solution: Use `numpy.percentile` with 'linear' interpolation method
- **Division by Zero in Coefficients**: D10 or D60 values of zero cause coefficient calculation failures. Solution: Check for zero values and handle edge cases with appropriate error messages
- **Unit Consistency Issues**: Mixing measurement units (μm vs mm) leads to incorrect classifications. Solution: Validate input ranges and include unit checks (typical grain sizes 1-1000 μm)
- **Insufficient Data Validation**: Small datasets (<10 grains) produce unreliable statistics. Solution: Implement minimum sample size checks and warn users about statistical reliability

## Error Handling
- Validate input data for non-negative values and reasonable grain size ranges (0.1-10000 μm)
- Handle empty or malformed input strings with clear error messages
- Check for minimum dataset size requirements for reliable statistical analysis
- Implement graceful handling of edge cases in coefficient calculations (zero denominators)
- Provide informative warnings for unusual distributions or outliers that may indicate measurement errors

## Quick Reference
