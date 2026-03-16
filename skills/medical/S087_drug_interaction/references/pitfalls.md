## Date Format Parsing Error

**Error**: ValueError: Unknown datetime string format, cannot parse
**Root Cause**: Pandas defaulting to MM/DD/YYYY format when data uses DD/MM/YYYY
**Fix**: Added multiple date format attempts with explicit format specification and dayfirst=True fallback

## Duplicate Interaction Records

**Error**: Same drug pair interactions appearing multiple times for one patient
**Root Cause**: Creating separate entries for every prescription pair within window instead of unique drug combinations
**Fix**: Modified logic to group by drug name first, then find closest concurrent prescriptions for each unique pair

## Performance Bottleneck

**Error**: Script taking over 10 minutes on 50,000 records
**Root Cause**: Nested loop approach with O(n²) complexity for concurrent medication detection
**Fix**: Optimized using pandas vectorized operations and processing unique drugs first to reduce comparisons

## Brand Name Interaction Misses

**Error**: Zero interactions found despite having interacting drugs in dataset
**Root Cause**: Interaction database using generic names while data contained brand names like "Coumadin" vs "warfarin"
**Fix**: Implemented comprehensive brand-to-generic drug name mapping system with partial matching

## CSV Timestamp Serialization Error

**Error**: TypeError: unhashable type: 'Timestamp' when writing CSV
**Root Cause**: CSV writer cannot handle pandas Timestamp objects directly
**Fix**: Convert Timestamp objects to strings using strftime() before CSV serialization
