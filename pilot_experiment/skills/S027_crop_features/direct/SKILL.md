# Agricultural Yield Prediction Feature Engineering

## Overview
This skill helps create a comprehensive feature engineering pipeline for crop yield prediction from field observation data, computing growing degree days, NDVI statistics, and correlation analysis for agricultural modeling.

## Workflow
1. Parse command line arguments for input CSV, output directory, and base temperature threshold
2. Load and validate field observation data, ensuring required columns and proper date formatting
3. Calculate Growing Degree Days (GDD) by computing daily thermal accumulation above base temperature for each field
4. Aggregate NDVI vegetation index statistics per field including mean, max, min, standard deviation, and peak date
5. Create comprehensive feature matrix combining all computed metrics with original field data
6. Compute Pearson correlation matrix to identify relationships between features and yield
7. Export results as CSV files and JSON summary with key agricultural insights

## Common Pitfalls
- **Date parsing errors**: Use `pd.to_datetime()` with error handling for malformed dates, and sort by date within each field before GDD calculations
- **Missing field grouping**: Always group by `field_id` before computing cumulative metrics like GDD to avoid cross-field contamination
- **Peak NDVI date format**: Convert datetime objects to string format (YYYY-MM-DD) before saving to avoid JSON serialization errors
- **Correlation with non-numeric data**: Exclude categorical columns like `crop_type` and `field_id` when computing correlation matrices
- **Empty output directory**: Use `os.makedirs(output_dir, exist_ok=True)` to create output directory if it doesn't exist

## Error Handling
- Validate input CSV contains all required columns before processing
- Handle missing values in numeric columns using forward fill or interpolation within field groups
- Check for empty dataframes after grouping operations and provide meaningful error messages
- Wrap correlation computation in try-catch to handle cases with insufficient numeric variance

## Quick Reference
