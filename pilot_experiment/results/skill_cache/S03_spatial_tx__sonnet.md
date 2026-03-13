# SKILL: Spatial Transcriptomics Data Preprocessing

## Overview
A Python CLI tool that preprocesses spatial transcriptomics count data by filtering low-expression genes, normalizing counts, applying log transformation, and selecting highly variable genes for downstream analysis.

## Workflow

1. **Parse Arguments & Load Data**
   - Use argparse to get input/output paths and n-top-genes parameter
   - Load CSV file with pandas, ensuring proper data types

2. **Separate Data Components**
   - Extract metadata columns (spot_id, x, y coordinates)
   - Isolate count matrix (numeric gene expression data)

3. **Filter Low-Expression Genes**
   - Remove genes expressed in fewer than 3 spots
   - Keep only genes with sufficient spatial coverage

4. **Normalize and Transform**
   - Scale each spot to total count of 10,000 (library size normalization)
   - Apply log1p transformation: log(count + 1)

5. **Select Highly Variable Genes**
   - Calculate variance for each gene across all spots
   - Select top N genes with highest variance

6. **Export Results**
   - Combine spot_id with processed count matrix
   - Save as CSV with spot_id as index

7. **Generate Summary Report**
   - Print spots count, genes before/after filtering, top 5 HVGs

## Common Pitfalls & Solutions

1. **Mixed Data Types in Count Matrix**
   - *Problem*: Non-numeric columns mixed with gene counts
   - *Solution*: Use `pd.to_numeric()` with `errors='coerce'` and explicitly separate metadata

2. **Zero-Sum Spots After Filtering**
   - *Problem*: Some spots have no remaining genes after filtering, causing division by zero
   - *Solution*: Remove spots with zero total counts before normalization

3. **Memory Issues with Large Datasets**
   - *Problem*: Loading entire matrix into memory fails
   - *Solution*: Use `dtype='float32'` and consider chunked processing for very large files

4. **Insufficient Highly Variable Genes**
   - *Problem*: Requesting more HVGs than available genes
   - *Solution*: Use `min(n_top_genes, len(filtered_genes))` to cap selection

## Error Handling Tips

- Validate file existence and readability before processing
- Check for required columns (spot_id) and warn about missing coordinates
- Handle empty datasets gracefully with informative error messages
- Verify numeric data ranges (negative counts should trigger warnings)
- Catch pandas parsing errors and suggest CSV format fixes

## Reference Code Snippet

```python
import pandas as pd
import numpy as np

def preprocess_spatial_data(df, n_top_genes=2000):
    # Separate metadata and counts
    metadata_cols = ['spot_id', 'x', 'y']
    metadata = df[metadata_cols].copy()
    counts = df.drop(columns=metadata_cols, errors='ignore')
    
    # Filter genes (expressed in >= 3 spots)
    gene_mask = (counts > 0).sum(axis=0) >= 3
    counts_filtered = counts.loc[:, gene_mask]
    
    # Normalize to 10k and log transform
    spot_totals = counts_filtered.sum(axis=1)
    counts_norm = counts_filtered.div(spot_totals, axis=0) * 10000
    counts_log = np.log1p(counts_norm)
    
    # Select highly variable genes
    gene_vars = counts_log.var(axis=0)
    top_genes = gene_vars.nlargest(min(n_top_genes, len(gene_vars))).index
    
    return counts_log[top_genes], metadata, gene_vars
```