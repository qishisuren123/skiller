# Phenological Shift Detection Analysis

## Overview
This skill enables detection and quantification of phenological shifts in long-term ecological time series data using advanced statistical methods including change-point detection, trend analysis, and climate correlation assessment.

## Workflow
1. **Data Ingestion and Validation**: Load time series data, validate required columns (year, DOY, temperature, precipitation), and perform initial data quality checks
2. **Data Preprocessing**: Handle missing values using interpolation/imputation, detect and treat outliers using IQR or z-score methods, and normalize climate variables
3. **Change-Point Detection**: Apply PELT algorithm and Mann-Kendall trend test to identify significant temporal shifts in phenological timing
4. **Climate Correlation Analysis**: Calculate Pearson/Spearman correlations between phenological events and climate variables with 0-3 year lag analysis
5. **Statistical Significance Testing**: Apply Benjamini-Hochberg correction for multiple comparisons and calculate confidence intervals for detected shifts
6. **Breakpoint Analysis**: Perform segmented regression to estimate exact timing and magnitude of shifts with uncertainty quantification
7. **Results Export**: Generate JSON report and visualization plots showing time series with detected change-points and trend lines

## Common Pitfalls
- **Insufficient data length**: Phenological analysis requires minimum 15-20 years of data for reliable change-point detection. Solution: Validate data length before analysis and warn users of insufficient temporal coverage
- **Ignoring autocorrelation**: Time series data often exhibits temporal autocorrelation that can inflate significance. Solution: Use modified Mann-Kendall test that accounts for autocorrelation structure
- **Climate lag oversimplification**: Assuming immediate climate effects without considering biological response delays. Solution: Implement systematic lag analysis testing 0-3 year delays for temperature and precipitation effects
- **Multiple comparison inflation**: Testing multiple change-points and climate variables inflates Type I error. Solution: Always apply Benjamini-Hochberg correction and report both raw and adjusted p-values
- **Outlier masking real shifts**: Aggressive outlier removal can eliminate genuine extreme events that represent phenological shifts. Solution: Use robust statistical methods and validate outliers against known ecological events

## Error Handling
- Validate input data format and required columns before processing
- Handle missing climate data using linear interpolation with maximum gap limits
- Implement fallback methods when primary algorithms fail (e.g., simple linear regression if segmented regression fails)
- Catch and report convergence failures in iterative algorithms with alternative parameter sets
- Validate statistical assumptions and warn users when assumptions are violated

## Quick Reference
