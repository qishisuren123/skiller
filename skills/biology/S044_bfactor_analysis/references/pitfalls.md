## JSON Serialization Error

**Error**: `TypeError: Object of type float64 is not JSON serializable`

**Root Cause**: NumPy data types (float64, int64) are not directly serializable to JSON format, causing the json.dump() function to fail when trying to save analysis results.

**Fix**: Explicitly convert all NumPy types to native Python types using float() and int() functions before JSON serialization. Ensure threshold value and segment boundaries are properly converted.

## Index Out of Range Error

**Error**: `IndexError: list index out of range` in create_bfactor_plot function

**Root Cause**: Confusion between 1-based residue numbering used for flexible_residues and 0-based array indexing needed for accessing bfactors list elements.

**Fix**: Properly convert between coordinate systems - use flexible_residues directly for plotting x-coordinates, but subtract 1 when indexing into bfactors array to get corresponding y-values.

## Segment Grouping Logic Verification

**Error**: Suspected incorrect grouping of consecutive flexible residues into segments

**Root Cause**: Initial concern about segment grouping algorithm not properly handling consecutive residue sequences.

**Fix**: Added logging to verify segment grouping logic works correctly. Algorithm properly extends segments for consecutive residues and creates new segments when gaps are encountered.
