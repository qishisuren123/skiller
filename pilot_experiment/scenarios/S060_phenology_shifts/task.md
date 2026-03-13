# Phenological Shift Detection Analysis

Create a CLI script that analyzes long-term ecological observation data to detect and quantify phenological shifts - changes in the timing of recurring biological events like flowering, migration, or breeding seasons.

Your script should accept time series data of phenological events and apply advanced statistical methods to detect significant temporal shifts, accounting for climate variables and natural variability.

## Requirements

1. **Data Processing**: Parse input time series data containing year, day-of-year (DOY) for phenological events, and associated temperature/precipitation data. Handle missing values and outliers using robust statistical methods.

2. **Trend Detection**: Implement multiple change-point detection algorithms (at minimum: PELT - Pruned Exact Linear Time, and Mann-Kendall trend test) to identify significant shifts in phenological timing over the time series.

3. **Climate Correlation Analysis**: Calculate correlations between phenological shifts and climate variables using both Pearson and Spearman methods. Implement lag analysis to account for delayed climate effects (0-3 year lags).

4. **Statistical Significance Testing**: Apply appropriate statistical tests to determine significance of detected shifts, including correction for multiple comparisons using Benjamini-Hochberg procedure. Calculate confidence intervals for shift magnitudes.

5. **Breakpoint Analysis**: For detected change-points, estimate the exact timing and magnitude of shifts using segmented regression. Quantify uncertainty in breakpoint locations.

6. **Output Generation**: Generate comprehensive JSON report containing detected shifts, statistical significance values, climate correlations, and breakpoint estimates. Create visualization plots showing time series with detected change-points and trend lines.

Use argparse for command-line interface with arguments for input data specification, output paths, significance thresholds, and analysis parameters.
