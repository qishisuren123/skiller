Write a Python CLI script for preprocessing spatial transcriptomics count data.

Input: A CSV file where rows are spots (spatial locations) and columns are genes. The first column is spot_id, and there may be columns "x" and "y" for spatial coordinates.

Requirements:
1. Use argparse: --input CSV path, --output processed CSV path, --n-top-genes (default 2000)
2. Load the CSV, separate count matrix from metadata (spot_id, x, y)
3. Filter out genes expressed in fewer than 3 spots
4. Normalize each spot to total count of 10000, then log1p transform
5. Select top N highly variable genes (by variance after normalization)
6. Save processed matrix as CSV with spot_id index
7. Print summary: number of spots, genes before/after filtering, top 5 HVGs
