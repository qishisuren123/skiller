# Common Pitfalls in Flood Frequency Analysis

## Column Name Whitespace Issue
**Error**: KeyError: 'station_id' when accessing DataFrame columns
**Root Cause**: CSV files often contain whitespace in column headers that are not visible
**Fix**: Strip whitespace from column names using `df.columns = df.columns.str.strip()`

## Non-finite Values in GEV Fitting
**Error**: ValueError: The data contains no finite values during GEV distribution fitting
**Root Cause**: Discharge data contains NaN, infinite, or negative values that break statistical fitting
**Fix**: Clean data by removing non-finite values: `df[np.isfinite(df['discharge_cms'])]` and validate positive flows

## Array Indexing Error in Baseflow Separation
**Error**: IndexError: index out of bounds during digital filter implementation
**Root Cause**: Incorrect array indexing when accessing discharge values in the digital filter loop
**Fix**: Use `.values` to extract numpy array and ensure proper indexing: `discharge_values = station_data['discharge_cms'].values`

## Insufficient Data for Statistical Analysis
**Error**: Unreliable or failed GEV parameter estimation
**Root Cause**: Too few years of annual maxima data for robust statistical fitting
**Fix**: Add validation to require minimum 5-10 years of data and warn users about reliability
