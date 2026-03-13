# Spatial Transcriptomics Data Preprocessing

## Overview
This skill helps preprocess spatial transcriptomics count data by filtering lowly expressed genes, normalizing spot counts, applying log transformation, and selecting highly variable genes for downstream analysis.

## Workflow
1. Parse command line arguments for input/output paths and number of top genes to select
2. Load CSV data and separate count matrix from spatial metadata (spot_id, x, y coordinates)
3. Filter genes expressed in fewer than 3 spots to remove noise
4. Normalize each spot's counts to 10,000 total counts (CPM-like normalization)
5. Apply log1p transformation to stabilize variance
6. Calculate gene variance and select top N highly variable genes (HVGs)
7. Save processed count matrix with spot_id as index and print processing summary

## Common Pitfalls
- **Mixed data types**: Ensure count columns are numeric before filtering - use `pd.to_numeric()` with `errors='coerce'`
- **Zero total counts**: Some spots may have zero total counts after filtering - handle division by zero in normalization
- **Memory issues with large datasets**: Use vectorized operations and avoid loops when calculating gene statistics
- **Incorrect variance calculation**: Calculate variance on normalized data, not raw counts, for proper HVG selection
- **Index preservation**: Maintain spot_id as index throughout processing to preserve spatial relationships

## Error Handling
- Validate input file exists and is readable CSV format
- Check for required columns (spot_id) and handle missing spatial coordinates gracefully
- Verify numeric data types for count matrix and convert if necessary
- Handle edge cases like all-zero genes or spots during filtering steps
- Ensure output directory exists before saving results

## Quick Reference
