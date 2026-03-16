## Nested Structure Access Error

**Error**: TypeError: string indices must be integers when accessing series data
**Root Cause**: Code attempted to access series-level fields (SeriesDate, Modality) directly on study-level records, but the data structure has series information nested within a Series array
**Fix**: Modified validation logic to iterate through the Series array and access series-level data within each series object using proper nested access patterns

## Memory Exhaustion with Large Datasets

**Error**: Out of memory errors when processing 10,000+ studies with multiple series
**Root Cause**: Loading entire dataset into memory at once and creating deep copies for anonymization consumed excessive memory
**Fix**: Implemented streaming processing with configurable batch sizes, incremental statistics calculation, and explicit garbage collection to manage memory usage efficiently

## Dictionary Modification During Iteration

**Error**: RuntimeError: dictionary changed size during iteration during anonymization
**Root Cause**: In-place modification of record dictionaries while they were being processed in the streaming iteration caused runtime conflicts
**Fix**: Replaced in-place modification with selective copying approach that creates new dictionaries with anonymized values while preserving memory efficiency compared to deep copying
