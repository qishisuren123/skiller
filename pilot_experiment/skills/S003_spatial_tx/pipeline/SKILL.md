# Spatial Transcriptomics Data Preprocessing CLI

## Overview
This skill helps create a robust Python CLI script for preprocessing spatial transcriptomics count data, including data loading, quality control, normalization, and highly variable gene selection with comprehensive error handling.

## Workflow
1. **Load and validate input data**
   - Read CSV file with pandas
   - Check for and remove duplicate column names
   - Separate metadata columns (spot_id, x, y) from count matrix

2. **Clean count data**
   - Handle missing values (NaN) by filling with zeros
   - Remove negative values by setting to zero
   - Convert all values to numeric, coercing non-numeric to zero

3. **Filter spots and genes**
   - Remove spots with zero total counts to avoid division by zero
   - Filter genes expressed in fewer than 3 spots
   - Validate that data remains after filtering

4. **Normalize and transform**
   - Normalize each spot to total count of 10,000
   - Apply log1p transformation
   - Filter out genes with zero variance

5. **Select highly variable genes**
   - Calculate variance for each gene
   - Select top N most variable genes
   - Handle cases where fewer genes are available than requested

6. **Save results**
   - Set spot_id as index
   - Save to CSV with proper index labeling

## Common Pitfalls
- **Duplicate gene names**: Use `~data.columns.duplicated()` to remove duplicates before processing
- **Zero total counts**: Filter spots before normalization to prevent ZeroDivisionError
- **Index alignment issues**: Use `.values` when setting index and `.loc` for consistent filtering
- **Extra index columns**: Use `index_label='spot_id'` in `to_csv()` to control output format
- **Zero variance genes**: Filter out genes with zero variance before highly variable gene selection
- **Shape mismatches**: Always use `.loc` for boolean indexing on both count matrix and metadata

## Error Handling
- **File loading**: Let pandas handle file not found errors naturally
- **Empty datasets**: Check for zero spots or genes after filtering and exit gracefully
- **Data type issues**: Use `pd.to_numeric(errors='coerce')` to handle mixed data types
- **Edge cases**: Validate that requested number of genes doesn't exceed available genes
- **Missing values**: Provide clear warnings when data cleaning occurs

## Quick Reference
