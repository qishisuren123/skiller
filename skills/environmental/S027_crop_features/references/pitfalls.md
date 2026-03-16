## Peak NDVI Date Index Mismatch

**Error**: KeyError when trying to find peak NDVI dates using idxmax() on grouped data
**Root Cause**: The idxmax() function returns original DataFrame indices that may not exist after sorting and grouping operations
**Fix**: Use groupby().apply() with custom function that finds max within each group, avoiding cross-group index references

## NaN Values in Standard Deviation

**Error**: NaN values appearing in ndvi_std column and propagating to correlation matrix
**Root Cause**: Fields with only one observation have undefined standard deviation, resulting in NaN
**Fix**: Use fillna(0.0) to replace NaN standard deviations with zero for single-observation fields

## Pandas Version Compatibility

**Error**: AttributeError when converting correlation series to dictionary using to_dict()
**Root Cause**: Different pandas versions handle the to_dict() method differently for Series objects
**Fix**: Manually iterate through series.items() and convert to dictionary with explicit type casting

## NumPy Correlation Broadcasting Error

**Error**: ValueError about broadcasting input array from shape (8,8) to shape (8,)
**Root Cause**: np.corrcoef() returns different shapes depending on input, causing DataFrame constructor issues
**Fix**: Use pandas corr() method consistently instead of mixing numpy and pandas correlation functions
