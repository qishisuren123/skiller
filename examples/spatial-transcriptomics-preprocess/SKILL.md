---
name: spatial-transcriptomics-preprocess
description: "对DLPFC空转数据集进行标准化预处理。数据由.csv, .h5, .txt等格式组成，需要经过整合、质量控制、归一化、高变基因选择、降维聚类等操作。使用scanpy和STAGATE_pyG工具包。数据来源: https://github.com/LieberInstitute/HumanPilot Use this skill when the user needs to 对dlpfc空转数据集进行标准化预处理。数据由.csv, .h5, .txt等格式组成，需要经过整合、质量控制、归一化、高变基因选择、降维聚类等操作。使用scanpy和stagate_pyg工具包。数."
license: MIT
compatibility: "Python >=3.9; scanpy, anndata, STAGATE_pyG, pandas, numpy, matplotlib"
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Spatial Transcriptomics Preprocess

## Overview
Comprehensive preprocessing pipeline for DLPFC spatial transcriptomics datasets. Handles multiple file formats (.csv, .h5, .txt), performs quality control, normalization, dimensionality reduction, and spatial-aware clustering using scanpy and STAGATE_pyG.

## When to Use
- Processing DLPFC spatial transcriptomics data from HumanPilot repository
- Need to integrate multiple file formats and samples
- Require spatial-aware analysis with STAGATE
- Want standardized preprocessing with quality control
- Need both traditional and spatial clustering approaches

## Inputs
- data_dir: Directory containing DLPFC files (*_filtered_feature_bc_matrix.h5, *_spatial_coordinates.csv, *_tissue_positions_list.csv)
- output_dir: Directory for saving processed results
- QC parameters: min_genes, max_genes, max_mt_pct for filtering
- Analysis parameters: n_neighbors, resolution for clustering
- STAGATE parameters: alpha, n_epochs, rad_cutoff for spatial analysis

## Workflow
1. Execute scripts/main.py with data directory path
2. Load 10X format files and spatial coordinates using scanpy
3. Perform quality control filtering based on references/workflow.md guidelines
4. Apply normalization, log transformation, and scaling
5. Run PCA, UMAP, and Leiden clustering
6. Execute STAGATE spatial analysis with optimized parameters
7. Generate comprehensive plots and save processed data

## Error Handling
The pipeline includes robust error handling for common issues. When STAGATE encounters memory or performance problems, the system will automatically subsample large datasets and adjust spatial network parameters. File format errors are handled by trying multiple scanpy readers (read_10x_h5 vs read_h5ad). Missing spatial coordinate files trigger warnings but allow processing to continue.

## Common Pitfalls
- Using wrong scanpy reader for 10X vs h5ad formats
- Losing raw data during normalization steps
- STAGATE performance issues on large datasets
- Aggressive filtering parameters removing too many spots
- Plotting function compatibility issues with scanpy versions

## Quick Reference

```bash
# Basic usage
python scripts/main.py --data-dir /path/to/DLPFC/ --output-dir ./results/

# With custom QC parameters
python scripts/main.py --data-dir /path/to/DLPFC/ --output-dir ./results/ \
    --min-genes 200 --max-genes 5000 --max-mt-pct 20 --resolution 0.5
```

```python
# Core preprocessing pattern
import scanpy as sc
adata = sc.read_10x_h5(h5_path)
adata.var_names_make_unique()
adata.obs['mt'] = adata.var_names.str.startswith('MT-')
sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)
sc.pp.filter_cells(adata, min_genes=200)
adata.raw = adata.copy()
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)
```

## Output Format
- Processed AnnData object with spatial coordinates in obsm['spatial']
- Quality control metrics in obs (total_counts, n_genes_by_counts, pct_counts_mt)
- Dimensionality reductions in obsm['X_pca'], obsm['X_umap']
- Clustering results in obs['leiden'], obs['leiden_stagate']
- STAGATE embeddings in obsm['STAGATE']
- Visualization plots saved as PNG files
- Final processed data saved as .h5ad file
