import argparse
import pandas as pd
import numpy as np
import sys

def preprocess_spatial_data(input_path, output_path, n_top_genes=2000):
    # Load the CSV file
    print(f"Loading data from {input_path}...")
    data = pd.read_csv(input_path)
    
    # Check for duplicate columns and handle them
    if data.columns.duplicated().any():
        print("Warning: Found duplicate gene names. Removing duplicates...")
        data = data.loc[:, ~data.columns.duplicated()]
    
    # Separate metadata from count matrix
    metadata_cols = ['spot_id']
    if 'x' in data.columns:
        metadata_cols.append('x')
    if 'y' in data.columns:
        metadata_cols.append('y')
    
    metadata = data[metadata_cols]
    count_matrix = data.drop(columns=metadata_cols)
    
    print(f"Loaded {count_matrix.shape[0]} spots and {count_matrix.shape[1]} genes")
    
    # Handle missing values
    nan_count = count_matrix.isna().sum().sum()
    if nan_count > 0:
        print(f"Warning: Found {nan_count} missing values. Filling with zeros...")
        count_matrix = count_matrix.fillna(0)
    
    # Handle negative values
    negative_mask = count_matrix < 0
    negative_count = negative_mask.sum().sum()
    if negative_count > 0:
        print(f"Warning: Found {negative_count} negative values. Setting to zero...")
        count_matrix = count_matrix.where(~negative_mask, 0)
    
    # Convert to numeric, handling any remaining non-numeric values
    count_matrix = count_matrix.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # Filter out spots with zero total counts
    spot_totals = count_matrix.sum(axis=1)
    valid_spots = spot_totals > 0
    if (~valid_spots).sum() > 0:
        print(f"Warning: Removing {(~valid_spots).sum()} spots with zero total counts")
        count_matrix = count_matrix.loc[valid_spots]
        metadata = metadata.loc[valid_spots]
        spot_totals = spot_totals[valid_spots]
    
    # Check if any spots remain
    if count_matrix.shape[0] == 0:
        print("Error: No valid spots remain after filtering!")
        sys.exit(1)
    
    genes_before = count_matrix.shape[1]
    
    # Filter genes expressed in fewer than 3 spots
    genes_expressed = (count_matrix > 0).sum(axis=0) >= 3
    count_matrix = count_matrix.loc[:, genes_expressed]
    genes_after = count_matrix.shape[1]
    
    # Check if any genes remain
    if genes_after == 0:
        print("Error: No genes remain after filtering!")
        sys.exit(1)
    
    # Normalize each spot to total count of 10000
    normalized_matrix = count_matrix.div(spot_totals, axis=0) * 10000
    
    # Log1p transform
    log_matrix = np.log1p(normalized_matrix)
    
    # Calculate variance and filter out zero-variance genes
    gene_vars = log_matrix.var(axis=0)
    variable_genes = gene_vars > 0
    zero_var_count = (~variable_genes).sum()
    
    if zero_var_count > 0:
        print(f"Warning: Removing {zero_var_count} genes with zero variance after normalization")
        gene_vars = gene_vars[variable_genes]
        log_matrix = log_matrix.loc[:, variable_genes]
    
    # Check if any variable genes remain
    if len(gene_vars) == 0:
        print("Error: No genes with variance > 0 remain after normalization!")
        sys.exit(1)
    
    # Select top N highly variable genes
    actual_n_genes = min(n_top_genes, len(gene_vars))
    
    if actual_n_genes < n_top_genes:
        print(f"Warning: Requested {n_top_genes} genes, but only {actual_n_genes} variable genes available")
    
    top_var_genes = gene_vars.nlargest(actual_n_genes).index
    final_matrix = log_matrix[top_var_genes]
    
    # Add spot_id as index
    final_matrix.index = metadata['spot_id'].values
    
    # Save processed matrix without extra index column
    final_matrix.to_csv(output_path, index_label='spot_id')
    
    # Print summary
    print(f"Number of spots: {final_matrix.shape[0]}")
    print(f"Genes before filtering: {genes_before}")
    print(f"Genes after filtering: {genes_after}")
    print(f"Selected {actual_n_genes} highly variable genes")
    print(f"Top 5 highly variable genes: {top_var_genes[:5].tolist()}")

def main():
    parser = argparse.ArgumentParser(description='Preprocess spatial transcriptomics count data')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    parser.add_argument('--n-top-genes', type=int, default=2000, help='Number of top variable genes to select')
    
    args = parser.parse_args()
    
    preprocess_spatial_data(args.input, args.output, args.n_top_genes)

if __name__ == "__main__":
    main()
