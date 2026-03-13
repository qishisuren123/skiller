# Gene Expression Data Processing CLI Tool

## Overview
This skill helps build a robust CLI tool for processing gene expression data that reads CSV expression files and FASTA sequence files, performs filtering and quantile normalization, and outputs processed results with comprehensive error handling.

## Workflow
1. **Setup argument parsing** with required input files (expression CSV, FASTA) and output directory
2. **Validate input files** exist before processing
3. **Read expression data** from CSV with genes as rows, samples as columns
4. **Parse FASTA sequences** efficiently by tracking sequence lengths rather than storing full sequences
5. **Find common genes** between expression and sequence data
6. **Filter low-expression genes** (default: mean TPM < 1)
7. **Perform quantile normalization** using vectorized operations for performance
8. **Calculate gene statistics** from filtered data for consistency
9. **Output results** including normalized expression matrix and gene statistics
10. **Handle edge cases** like constant values, zero variance, and insufficient data

## Common Pitfalls
- **FASTA parsing bug**: Forgetting to process the last sequence after the loop ends
- **Quantile normalization errors**: Using wrong axis or incorrect ranking logic - normalize across samples (columns), not genes
- **Performance issues**: Using nested loops instead of vectorized operations for large datasets
- **Index errors**: Fractional ranks from ties causing array index problems - use `np.clip()` to handle edge cases
- **Data inconsistency**: Calculating statistics from original data but only including filtered genes in output
- **Memory issues**: Storing full sequences instead of just lengths for large FASTA files
- **Gene mismatch**: Not handling cases where genes exist in one file but not the other

## Error Handling
- **File validation**: Check file existence before processing
- **Empty data checks**: Validate dataframes aren't empty after each filtering step
- **Common genes validation**: Ensure at least some genes overlap between files
- **Correlation requirements**: Check for minimum data points before calculating correlations
- **Edge case handling**: Manage constant values, zero variance samples, and ranking edge cases
- **Memory optimization**: Use length tracking instead of full sequence storage for FASTA files

## Quick Reference
