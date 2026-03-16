# Common Pitfalls and Solutions

## Scipy Function Name Error
**Error**: AttributeError: module 'scipy.stats' has no attribute 'linregr'
**Root Cause**: Incorrect function name used for linear regression in scipy.stats
**Fix**: Use `stats.linregress()` instead of `stats.linregr()` - the correct function name includes the full word "linregress"

## JSON Serialization Error with Timestamps  
**Error**: TypeError: Object of type Timestamp is not JSON serializable
**Root Cause**: Pandas Timestamp objects in DataFrame index cannot be directly serialized to JSON
**Fix**: Convert timestamps to strings using strftime('%Y-%m-%d') before creating the JSON dictionary structure, and explicitly cast numpy types to Python native types (int, float)

## Performance Issues with Large Datasets
**Error**: Slow processing times when using daily periods with thousands of documents
**Root Cause**: Inefficient pandas groupby operations and memory-intensive DataFrame manipulations
**Fix**: Replace groupby with pd.crosstab for faster counting, use period extraction (dt.date, dt.to_period) instead of resampling, and process only necessary columns to reduce memory usage
