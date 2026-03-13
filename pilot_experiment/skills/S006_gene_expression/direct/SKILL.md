# Gene Expression Data Processing with Sequence Analysis

## Overview
This skill enables processing of gene expression data (TPM values) with associated sequence information, including filtering, quantile normalization, and statistical analysis of expression-sequence relationships.

## Workflow
1. Parse command-line arguments for input files (expression CSV, FASTA sequences) and output directory
2. Load expression matrix and filter genes with mean TPM < 1 across all samples
3. Apply quantile normalization to expression data across samples to remove technical variation
4. Parse FASTA file to extract gene names and calculate sequence lengths
5. Merge expression statistics with sequence length data for filtered genes
6. Export normalized expression matrix and comprehensive gene statistics to output directory
7. Calculate and report summary statistics including expression-length correlation

## Common Pitfalls
- **Gene name mismatch**: Expression CSV columns and FASTA headers may use different naming conventions (e.g., gene symbols vs IDs). Solution: Implement flexible matching and report unmatched genes.
- **Memory issues with large matrices**: Expression data can be memory-intensive. Solution: Use pandas chunking for very large files and specify appropriate dtypes.
- **Quantile normalization edge cases**: Genes with identical expression values can cause ranking issues. Solution: Use scipy.stats.rankdata with 'average' method for tie handling.
- **FASTA parsing errors**: Malformed FASTA entries or multi-line sequences. Solution: Use robust parsing that handles line breaks and validates sequence format.
- **Missing output directory**: Script fails if output directory doesn't exist. Solution: Create directory structure using os.makedirs with exist_ok=True.

## Error Handling
- Validate file existence and readability before processing
- Check for empty datasets after filtering and provide informative messages
- Handle gene name mismatches gracefully with detailed logging
- Implement data type validation for expression values (numeric, non-negative)
- Catch and report correlation calculation errors when insufficient data remains

## Quick Reference
