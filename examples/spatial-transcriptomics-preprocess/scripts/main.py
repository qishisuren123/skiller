#!/usr/bin/env python3
"""
DLPFC Spatial Transcriptomics Preprocessing Pipeline
Handles loading, QC, normalization, dimensionality reduction, and spatial analysis
"""

import scanpy as sc
import anndata as ad
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import STAGATE_pyG
try:
    import STAGATE_pyG as STAGATE
    import torch
    STAGATE_AVAILABLE = True
    logger.info("STAGATE_pyG imported successfully")
except ImportError:
    STAGATE_AVAILABLE = False
    logger.warning("STAGATE_pyG not available")

def load_dlpfc_data(data_dir):
    """Load DLPFC spatial transcriptomics data from 10X format"""
    
    sc.settings.verbosity = 3
    sc.settings.set_figure_params(dpi=80, facecolor='white')
    
    data_path = Path(data_dir)
    adata_list = []
    
    h5_files = list(data_path.glob("*filtered_feature_bc_matrix.h5"))
    h5ad_files = list(data_path.glob("*.h5ad"))

    # 优先加载 10X h5 格式，如果没有则尝试 h5ad
    if h5_files:
        for h5_file in h5_files:
            sample_id = h5_file.stem.replace("_filtered_feature_bc_matrix", "")
            logger.info(f"Loading sample {sample_id}")

            adata = sc.read_10x_h5(h5_file)
            adata.var_names_unique()

            spatial_coords_file = data_path / f"{sample_id}_spatial_coordinates.csv"
            if spatial_coords_file.exists():
                spatial_coords = pd.read_csv(spatial_coords_file, index_col=0)
                common_barcodes = adata.obs.index.intersection(spatial_coords.index)
                adata = adata[common_barcodes, :]
                adata.obsm['spatial'] = spatial_coords.loc[common_barcodes, ['x', 'y']].values

            tissue_pos_file = data_path / f"{sample_id}_tissue_positions_list.csv"
            if tissue_pos_file.exists():
                tissue_pos = pd.read_csv(tissue_pos_file, index_col=0)
                common_barcodes = adata.obs.index.intersection(tissue_pos.index)
                adata = adata[common_barcodes, :]
                for col in tissue_pos.columns:
                    adata.obs[col] = tissue_pos.loc[common_barcodes, col]

            adata.obs['sample_id'] = sample_id
            adata_list.append(adata)
    elif h5ad_files:
        for h5ad_file in h5ad_files:
            sample_id = h5ad_file.stem
            logger.info(f"Loading h5ad sample {sample_id}")
            adata = sc.read_h5ad(h5ad_file)
            adata.var_names_make_unique()
            adata.obs['sample_id'] = sample_id
            adata_list.append(adata)
    else:
        raise FileNotFoundError(f"No .h5 or .h5ad files found in {data_dir}")
    
    if len(adata_list) > 1:
        adata_combined = ad.concat(adata_list, axis=0, join='outer')
    else:
        adata_combined = adata_list[0]
    
    adata_combined.var_names_make_unique()
    return adata_combined

def quality_control_and_filtering(adata, min_genes=100, min_cells=5, max_genes=8000, max_mt_pct=25):
    """Perform quality control and filtering"""
    
    logger.info("Starting QC and filtering...")
    logger.info(f"Initial data shape: {adata.shape}")
    
    adata.var['mt'] = adata.var_names.str.startswith('MT-')
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)
    
    adata.raw = adata.copy()
    
    sc.pp.filter_cells(adata, min_genes=min_genes)
    sc.pp.filter_cells(adata, max_genes=max_genes)
    sc.pp.filter_genes(adata, min_cells=min_cells)
    adata = adata[adata.obs.pct_counts_mt < max_mt_pct, :]
    
    logger.info(f"After filtering shape: {adata.shape}")
    return adata

def normalize_and_scale(adata):
    """Normalize and scale the data"""
    
    logger.info("Normalizing and scaling data...")
    
    raw_backup = adata.copy()
    
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)

    # 保存归一化后的完整数据到 .raw，再过滤高变基因
    adata.raw = adata.copy()
    adata = adata[:, adata.var.highly_variable]
    sc.pp.scale(adata, max_value=10)

    return adata

def dimensionality_reduction_and_clustering(adata, n_comps=50, n_neighbors=15, resolution=0.5):
    """Perform PCA, UMAP, and clustering"""
    
    logger.info("Performing dimensionality reduction and clustering...")
    
    sc.tl.pca(adata, svd_solver='arpack', n_comps=n_comps)
    sc.pp.neighbors(adata, n_neighbors=n_neighbors, n_pcs=40)
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=resolution, key_added='leiden')
    
    logger.info(f"Found {len(adata.obs['leiden'].unique())} clusters")
    
    return adata

def run_stagate_analysis(adata, alpha=0.5, n_epochs=500, rad_cutoff=150):
    """Run STAGATE spatial analysis"""
    
    if not STAGATE_AVAILABLE:
        logger.warning("STAGATE_pyG not available, skipping spatial analysis")
        return adata
    
    logger.info("Running STAGATE spatial analysis...")
    
    adata_stagate = adata.copy()
    
    if 'raw_filtered' in adata.layers:
        adata_stagate.X = adata.layers['raw_filtered']
    else:
        logger.warning("Using normalized data for STAGATE")
        adata_stagate.X = adata.raw.X
    
    if adata_stagate.n_obs > 5000:
        logger.info(f"Subsampling large dataset for STAGATE")
        sc.pp.subsample(adata_stagate, n_obs=3000, random_state=42)
    
    STAGATE.Cal_Spatial_Net(adata_stagate, rad_cutoff=rad_cutoff)
    STAGATE.Stats_Spatial_Net(adata_stagate)
    
    adata_stagate = STAGATE.train_STAGATE(adata_stagate, alpha=alpha, n_epochs=n_epochs, 
                                         lr=0.001, weight_decay=1e-4, random_seed=0)
    
    adata.obsm['STAGATE'] = adata_stagate.obsm['STAGATE']
    sc.pp.neighbors(adata, use_rep='STAGATE')
    sc.tl.leiden(adata, resolution=0.5, key_added='leiden_stagate')
    
    logger.info(f"STAGATE found {len(adata.obs['leiden_stagate'].unique())} spatial clusters")
    
    return adata

def plot_results(adata, save_dir=None):
    """Plot analysis results"""
    import matplotlib
    matplotlib.use('Agg')  # 非交互模式

    try:
        sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50, show=False)
    except TypeError:
        sc.pl.pca_variance_ratio(adata, log=True, n_pcs=50, show=False)
    if save_dir:
        plt.savefig(f"{save_dir}/pca_variance.png", dpi=150, bbox_inches='tight')
    plt.close()

    sc.pl.umap(adata, color='leiden', show=False)
    if save_dir:
        plt.savefig(f"{save_dir}/umap_leiden.png", dpi=150, bbox_inches='tight')
    plt.close()

    sc.pl.umap(adata, color='sample_id', show=False)
    if save_dir:
        plt.savefig(f"{save_dir}/umap_sample.png", dpi=150, bbox_inches='tight')
    plt.close()

    logger.info(f"Plots saved to {save_dir or 'current dir'}")

def main():
    parser = argparse.ArgumentParser(description='DLPFC Spatial Transcriptomics Preprocessing')
    parser.add_argument('--data_dir', required=True, help='Directory containing DLPFC data files')
    parser.add_argument('--output_dir', required=True, help='Output directory for results')
    parser.add_argument('--min_genes', type=int, default=100, help='Minimum genes per spot')
    parser.add_argument('--max_genes', type=int, default=8000, help='Maximum genes per spot')
    parser.add_argument('--max_mt_pct', type=float, default=25, help='Maximum mitochondrial gene percentage')
    parser.add_argument('--resolution', type=float, default=0.5, help='Clustering resolution')
    parser.add_argument('--n_epochs', type=int, default=500, help='STAGATE training epochs')
    parser.add_argument('--skip_stagate', action='store_true', help='Skip STAGATE analysis')
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    logger.info("=== Loading Data ===")
    adata = load_dlpfc_data(args.data_dir)
    logger.info(f"Loaded data shape: {adata.shape}")
    
    logger.info("=== Quality Control ===")
    adata_filtered = quality_control_and_filtering(adata, args.min_genes, 5, 
                                                 args.max_genes, args.max_mt_pct)
    
    logger.info("=== Normalization ===")
    adata_processed = normalize_and_scale(adata_filtered)
    
    logger.info("=== Dimensionality Reduction & Clustering ===")
    adata_processed = dimensionality_reduction_and_clustering(adata_processed, 
                                                            resolution=args.resolution)
    
    if not args.skip_stagate:
        logger.info("=== STAGATE Spatial Analysis ===")
        adata_processed = run_stagate_analysis(adata_processed, n_epochs=args.n_epochs)
    
    logger.info("=== Plotting Results ===")
    plot_results(adata_processed, args.output_dir)
    
    adata_processed.write(f"{args.output_dir}/dlpfc_processed.h5ad")
    logger.info(f"Processed data saved to {args.output_dir}/dlpfc_processed.h5ad")
    logger.info(f"Final data shape: {adata_processed.shape}")

if __name__ == "__main__":
    main()
