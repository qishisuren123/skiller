## Scipy Dependency Error
**Error**: ModuleNotFoundError when importing scipy.stats.fisher_exact
**Root Cause**: Scipy not installed in environment, only numpy available
**Fix**: Implemented manual Fisher's exact test using log factorials to avoid overflow

## Contingency Table Construction Error  
**Error**: ValueError with negative values in contingency table cells
**Root Cause**: Incorrect subtraction of input_count from background_count when input genes are subset of background
**Fix**: Properly separate background genes into input vs background-only sets before counting

## Low Enrichment Ratios
**Error**: All enrichment ratios < 1.0 even for enriched terms
**Root Cause**: Using background-only counts instead of total background in expected frequency calculation
**Fix**: Calculate expected frequency using total background gene count while maintaining proper contingency table

## Performance Issues with Large Datasets
**Error**: Script hangs during Fisher's exact test with 100+ genes
**Root Cause**: Manual Fisher's exact test has exponential complexity for large contingency tables
**Fix**: Added chi-square approximation with automatic fallback to Fisher's test for small expected values
