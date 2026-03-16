## Path Object Conversion Error

**Error**: `AttributeError: 'str' object has no attribute 'suffix'` when trying to check file extension

**Root Cause**: The argparse input was passed as string but code expected Path object with suffix attribute

**Fix**: Added explicit conversion `filepath = Path(filepath)` in load_data method before checking suffix

## Column Name Mismatch Error

**Error**: `ValueError: Missing required columns: ['temperature', 'precipitation']` despite having climate data

**Root Cause**: User data had columns named 'temp_spring' and 'precip_spring' but code expected exact matches

**Fix**: Implemented flexible column mapping that detects columns containing 'temp' or 'precip' substrings and automatically renames them

## Changepoint Index Out of Bounds Error

**Error**: `IndexError: index 42 out of bounds for axis 0 with size 35` during changepoint year conversion

**Root Cause**: PELT algorithm returns array indices (0-based) but code tried to use them directly as pandas Series indices without proper conversion

**Fix**: Added proper index conversion using `series.iloc[cp_idx:cp_idx+1].index[0]` with bounds checking to map array positions to actual years

## Missing Statistical Corrections

**Error**: Multiple comparison problem leading to inflated Type I error rates in correlation analysis

**Root Cause**: Original implementation performed multiple correlation tests without adjusting for multiple comparisons

**Fix**: Implemented Benjamini-Hochberg correction using `multipletests()` from statsmodels, collecting all p-values and applying FDR correction
