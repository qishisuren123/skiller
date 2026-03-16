1. **Data Loading and Validation**
   - Load CSV/Excel files with flexible column name detection
   - Automatically map temperature/precipitation column variants
   - Validate presence of required columns (year, doy, climate variables)
   - Sort data chronologically by year

2. **Data Preprocessing**
   - Remove rows with missing year or day-of-year values
   - Interpolate missing climate data using linear interpolation
   - Detect outliers using IQR method but preserve them for analysis
   - Flag potential data quality issues

3. **PELT Changepoint Detection**
   - Apply Pruned Exact Linear Time algorithm with RBF kernel
   - Convert array indices to actual years with bounds checking
   - Use configurable penalty parameter to control sensitivity
   - Minimum segment size of 3 years to ensure statistical validity

4. **Segmented Regression Analysis**
   - Fit linear regression models to each segment between changepoints
   - Calculate 95% confidence intervals for slope estimates
   - Compute R-squared values and mean squared error for each segment
   - Handle single segment case (no changepoints detected)

5. **Mann-Kendall Trend Testing**
   - Perform non-parametric trend test on full time series
   - Calculate test statistic, Z-score, and p-value
   - Classify trend direction (increasing/decreasing/no trend)

6. **Climate Correlation Analysis**
   - Calculate Pearson and Spearman correlations with lag analysis (0-3 years)
   - Apply Benjamini-Hochberg correction for multiple comparisons
   - Handle missing data in lagged correlations appropriately

7. **Results Export and Summary**
   - Export comprehensive results to JSON format
   - Include statistical summaries and data quality metrics
   - Provide command-line summary of key findings
