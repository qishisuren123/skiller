# DLPFC Spatial Transcriptomics Preprocessing Workflow

## Step 1: Data Loading
- Identify 10X format files (*_filtered_feature_bc_matrix.h5)
- Load spatial coordinates from CSV files
- Load tissue position information
- Combine multiple samples into single AnnData object

## Step 2: Quality Control
- Calculate QC metrics (total counts, gene counts, mitochondrial percentage)
- Filter spots with too few genes (min_genes=100)
- Filter spots with too many genes (max_genes=8000) 
- Filter genes expressed in too few spots (min_cells=5)
- Remove spots with high mitochondrial content (max_mt_pct=25%)

## Step 3: Normalization
- Preserve raw data before normalization
- Normalize total counts to 10,000 per spot
- Log transform the data
- Identify highly variable genes
- Scale data to unit variance

## Step 4: Dimensionality Reduction
- Perform PCA with 50 components
- Build neighborhood graph with 15 neighbors
- Generate UMAP embedding
- Perform Leiden clustering

## Step 5: Spatial Analysis
- Prepare raw filtered data for STAGATE
- Calculate spatial network with radius cutoff
- Train STAGATE model for spatial embeddings
- Perform spatial-aware clustering

## Step 6: Visualization and Output
- Generate comprehensive plots (PCA, UMAP, spatial)
- Save processed data as h5ad file
- Export visualization plots as PNG files
