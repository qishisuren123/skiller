#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
import sys
from pathlib import Path

def load_and_separate_data(input_path):
    """Load CSV and separate count matrix from metadata."""
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        sys.exit(1)
    
    if 'spot_id' not in df.columns:
        print("Error: 'spot_id' column not found in input file")
        sys.exit(1)
    
    # Identify metadata columns
    metadata_cols = ['spot_id']
    if 'x' in df.columns:
        metadata_cols.append('x')
    if 'y' in df.columns:
        metadata_cols.append('y')
    
    # Separate metadata and count matrix
    metadata = df[metadata_cols].copy()
    count_cols = [col for col in df.columns if col not in metadata_cols]
    counts = df[count_cols].copy()
    
    # Convert counts to numeric, handling any non-numeric values
    for col in count_cols:
        counts[col] = pd.to_numeric(counts[col], errors='coerce')
    
    # Fill NaN values with 0
    counts = counts.fillna(0)
    
    # Set spot_id as index
    counts.index = metadata['spot_id']
    
    return counts, metadata

def filter_genes(counts, min_spots=3):
    """Filter genes expressed in fewer than min_spots."""
    # Count non-zero expression per gene
    gene_spot_counts = (counts > 0).sum(axis=0)
    valid_genes = gene_spot_counts >= min_spots
    
    return counts.loc[:, valid_genes]

def normalize_and_transform(counts, target_sum=10000):
    """Normalize to target sum and apply log1p transformation."""
    # Calculate total counts per spot
    spot_totals = counts.sum(axis=1)
    
    # Handle spots with zero total counts
    spot_totals = spot_totals.replace(0, 1)  # Avoid division by zero
    
    # Normalize to target sum
    normalized = counts.div(spot_totals, axis=0) * target_sum
    
    # Apply log1p transformation
    log_transformed = np.log1p(normalized)
    
    return log_transformed

def select_hvgs(normalized_counts, n_top_genes):
    """Select top highly variable genes based on variance."""
    # Calculate variance for each gene
    gene_vars = normalized_counts.var(axis=0)
    
    # Select top N genes by variance
    n_genes_available = len(gene_vars)
    n_select = min(n_top_genes, n_genes_available)
    
    top_genes = gene_vars.nlargest(n_select).index
    hvg_matrix = normalized_counts[top_genes]
    
    return hvg_matrix, gene_vars.sort_values(ascending=False)

def print_summary(original_counts, filtered_counts, final_counts, gene_vars):
    """Print processing summary statistics."""
    n_spots = original_counts.shape[0]
    n_genes_original = original_counts.shape[1]
    n_genes_filtered = filtered_counts.shape[1]
    n_genes_final = final_counts.shape[1]
    
    print(f"\nProcessing Summary:")
    print(f"Number of spots: {n_spots}")
    print(f"Genes before filtering: {n_genes_original}")
    print(f"Genes after filtering: {n_genes_filtered}")
    print(f"Final genes selected: {n_genes_final}")
    
    print(f"\nTop 5 highly variable genes:")
    top_5_hvgs = gene_vars.head(5)
    for i, (gene, variance) in enumerate(top_5_hvgs.items(), 1):
        print(f"{i}. {gene}: {variance:.4f}")

def main():
    parser = argparse.ArgumentParser(
        description="Preprocess spatial transcriptomics count data"
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Input CSV file path"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Output processed CSV file path"
    )
    parser.add_argument(
        "--n-top-genes", 
        type=int, 
        default=2000,
        help="Number of top highly variable genes to select (default: 2000)"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' does not exist")
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading data from {args.input}...")
    counts, metadata = load_and_separate_data(args.input)
    original_counts = counts.copy()
    
    print("Filtering lowly expressed genes...")
    filtered_counts = filter_genes(counts, min_spots=3)
    
    print("Normalizing and transforming data...")
    normalized_counts = normalize_and_transform(filtered_counts)
    
    print(f"Selecting top {args.n_top_genes} highly variable genes...")
    final_counts, gene_vars = select_hvgs(normalized_counts, args.n_top_genes)
    
    print(f"Saving processed data to {args.output}...")
    # Save with spot_id as the first column (reset index)
    output_df = final_counts.reset_index()
    output_df.to_csv(args.output, index=False)
    
    print_summary(original_counts, filtered_counts, final_counts, gene_vars)
    print(f"\nProcessing complete! Output saved to {args.output}")

if __name__ == "__main__":
    main()
