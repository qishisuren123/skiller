# Heat Index Analysis and Heat Wave Detection

## Overview
This skill enables processing of atmospheric temperature and humidity data to calculate accurate heat index time series using the National Weather Service formula, detect heat wave events based on climatological thresholds, and perform comprehensive statistical analysis including trend detection and return period estimation.

## Workflow
1. **Data Loading and Validation**: Load temperature and humidity CSV files, validate datetime formats, check for missing values, and ensure temporal alignment between datasets
2. **Heat Index Calculation**: Implement the full NWS heat index formula with all adjustment factors, handling edge cases for extreme humidity conditions and temperature ranges
3. **Climatological Baseline Construction**: Build rolling climatology using specified baseline years with 15-day windows centered on each day-of-year to calculate percentile thresholds
4. **Heat Wave Event Detection**: Identify consecutive periods exceeding threshold for minimum duration, merge events separated by single days, and extract event boundaries
5. **Statistical Analysis**: Calculate heat wave metrics (duration, intensity, cumulative excess heat), estimate return periods, and perform trend analysis with significance testing
6. **Temporal Trend Computation**: Apply linear regression to decadal heat wave statistics, compute confidence intervals and test statistical significance of trends
7. **Output Generation**: Save complete heat index time series with metadata and structured JSON output containing all heat wave events and statistical results

## Common Pitfalls
- **Heat Index Formula Complexity**: The NWS formula has multiple adjustment factors that are often omitted. Always include the Rothfusz adjustments for low/high humidity and the simple formula fallback for temperatures below 80°F
- **Climatological Window Edge Effects**: When calculating day-of-year climatology, handle year boundaries properly by wrapping the 15-day window (e.g., Jan 1 includes Dec 24-31 from previous years)
- **Heat Wave Merging Logic**: Single-day breaks in heat waves should be merged, but be careful not to merge events with longer gaps. Implement proper gap detection before merging consecutive events
- **Missing Data Handling**: Temperature and humidity datasets may have different missing data patterns. Interpolate short gaps but exclude periods with insufficient data from heat wave detection
- **Return Period Estimation**: Use proper extreme value statistics (Gumbel distribution) rather than simple frequency counting, and account for the limited sample size in confidence interval estimation

## Error Handling
- Validate input file formats and handle CSV parsing errors with informative messages
- Check for sufficient overlapping data between temperature and humidity time series
- Handle mathematical edge cases in heat index calculation (extreme values, division by zero)
- Implement robust trend analysis that handles insufficient data periods
- Provide clear error messages for invalid parameter combinations (e.g., baseline period longer than available data)

## Quick Reference
