# Common Pitfalls and Solutions

## Empty Sequence Error in AQI Calculation
**Error**: ValueError: max() arg is an empty sequence
**Root Cause**: All sub-indices returned NaN due to insufficient data coverage or missing values
**Fix**: Added validation for empty sequences and data coverage requirements (75% minimum for daily averages)

## Date Format Mismatch in Exceedance Report
**Error**: AttributeError: 'Series' object has no attribute 'dt'
**Root Cause**: Mixing date objects with datetime operations - stored dates as date objects but tried to use dt.strftime()
**Fix**: Convert date columns to datetime objects before using pandas datetime accessor methods

## Insufficient Data Coverage
**Error**: All daily AQI values coming back as NaN
**Root Cause**: Not enough hourly measurements to meet EPA data completeness requirements
**Fix**: Implemented minimum data coverage thresholds (18 hours for 24-hour averages, 6 periods for 8-hour rolling)

## Rolling Window Calculation Failures
**Error**: Rolling averages returning NaN for sparse data
**Root Cause**: Default rolling window requires all periods to be present
**Fix**: Added min_periods parameter to rolling calculations to handle gaps in data
