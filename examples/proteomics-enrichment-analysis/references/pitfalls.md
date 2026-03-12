# Common Pitfalls and Solutions

## Error 1: scipy.stats ImportError
**Error**: `ImportError: cannot import name 'false_discovery_control' from 'scipy.stats'`
**Root Cause**: Using older scipy version that doesn't have false_discovery_control function
**Fix**: Implemented manual Benjamini-Hochberg correction function to maintain compatibility with older scipy versions

## Error 2: Missing Function Definitions
**Error**: `NameError: name 'perform_ttest' is not defined`
**Root Cause**: Functions were accidentally removed when adding new code sections
**Fix**: Ensured all required functions are included in the complete script and maintained proper function dependencies

## Error 3: UniProt API Timeout Issues
**Error**: API calls taking 20+ minutes and timing out
**Root Cause**: Inefficient API usage with individual requests instead of batch processing
**Fix**: Implemented optimized batch processing with proper rate limiting and timeout handling using UniProt's new REST API endpoints

## Error 4: KEGG API Type Error
**Error**: `TypeError: sequence item 0: expected str, but list found`
**Root Cause**: Trying to join a list containing other lists in pathway name retrieval
**Fix**: Fixed data structure handling and added proper type checking before string operations

## Error 5: KEGG API Timeouts and Rate Limiting
**Error**: KEGG API calls failing with timeouts and 403 errors
**Root Cause**: Exceeding KEGG API rate limits and not handling network timeouts properly
**Fix**: Added exponential backoff retry logic, reduced batch sizes, implemented proper timeout handling, and added graceful failure recovery

## Error 6: Memory Issues with Large Datasets
**Error**: Out of memory errors when processing thousands of proteins
**Root Cause**: Loading all data into memory simultaneously and inefficient data structures
**Fix**: Implemented streaming processing, batch operations, and memory-efficient data handling for large protein datasets
