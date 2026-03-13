# Gene Expression Data Processing Tool

## Overview
A Python CLI tool that processes gene expression data alongside sequence information. It filters low-expression genes, performs quantile normalization, and generates statistical summaries linking expression levels to sequence characteristics.

## Workflow

1. **Parse command-line arguments** using argparse for input files and output directory
2. **Load expression matrix** from CSV file with samples as rows and genes as columns
3. **Filter genes** by removing those with mean TPM < 1 across all samples
4. **Apply quantile normalization** to expression matrix across samples to reduce technical variation
5. **Parse FASTA sequences** to extract gene names and calculate sequence lengths
6. **Generate output files**: normalized expression matrix and gene statistics table
7. **Calculate and display summary** including sample/gene counts and expression-length correlation

## Common Pitfalls & Solutions

1. **Mismatched gene identifiers between files**
   - Solution: Use set intersection to work only with genes present in both files; log missing genes

2. **Memory issues with large expression matrices**
   - Solution: Use pandas chunking or numpy memory mapping for very large datasets

3. **FASTA parsing errors with malformed headers**
   - Solution: Strip whitespace and validate header format; skip malformed entries with warnings

4. **Division by zero in quantile normalization**
   - Solution: Add small epsilon (1e-8) to avoid zero values or handle zero columns separately

5. **Output directory permissions or existence**
   - Solution: Use `os.makedirs(exist_ok=True)` and check write permissions before processing

## Error Handling Tips

- Validate file existence and readability before processing
- Check for empty dataframes after filtering step
- Ensure FASTA sequences contain valid nucleotides/amino acids
- Handle NaN values in expression data explicitly
- Wrap file I/O operations in try-except blocks with informative error messages

## Reference Code Snippet

```python
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def quantile_normalize(df):
    """Quantile normalize expression matrix across samples"""
    rank_mean = df.stack().groupby(df.rank(method='first').stack().astype(int)).mean()
    normalized = df.rank(method='min').stack().astype(int).map(rank_mean).unstack()
    return normalized

def process_expression_data(expression_file, fasta_file, output_dir):
    # Load and filter expression data
    expr_df = pd.read_csv(expression_file, index_col=0)
    gene_means = expr_df.mean(axis=0)
    filtered_genes = gene_means[gene_means >= 1.0].index
    expr_filtered = expr_df[filtered_genes]
    
    # Quantile normalize
    expr_normalized = quantile_normalize(expr_filtered)
    
    # Parse FASTA and calculate stats
    seq_lengths = {}
    with open(fasta_file, 'r') as f:
        gene_name = None
        for line in f:
            if line.startswith('>'):
                gene_name = line[1:].strip()
            elif gene_name:
                seq_lengths[gene_name] = len(line.strip())
    
    # Generate statistics and correlation
    common_genes = set(expr_normalized.columns) & set(seq_lengths.keys())
    correlation, _ = pearsonr(
        [expr_normalized[g].mean() for g in common_genes],
        [seq_lengths[g] for g in common_genes]
    )
    
    return expr_normalized, seq_lengths, correlation
```