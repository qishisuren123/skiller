#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
from scipy import stats
import os

def parse_fasta(fasta_file):
    """Parse FASTA file and return dict of gene_name -> sequence_length"""
    sequences = {}
    with open(fasta_file, 'r') as f:
        current_gene = None
        current_seq_length = 0  # Track length instead of storing full sequence
        for line in f:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            if line.startswith('>'):
                if current_gene:
                    sequences[current_gene] = current_seq_length
                current_gene = line[1:].strip()
                current_seq_length = 0
            else:
                current_seq_length += len(line)
        # Don't forget the last sequence!
        if current_gene:
            sequences[current_gene] = current_seq_length
    return sequences

def quantile_normalize(df):
    """Quantile normalize expression matrix across samples (columns) - vectorized version"""
    if df.empty:
        return df
    
    # Convert to numpy for faster operations
    data = df.values.copy()
    
    # Sort each column (sample) independently
    sorted_data = np.sort(data, axis=0)
    # Calculate the mean of each rank across all samples
    rank_means = np.mean(sorted_data, axis=1)
    
    # Get ranks for each value (1-based, average method for ties)
    ranks = df.rank(method='average').values
    
    # Convert ranks to 0-based indices and clip to valid range
    indices = np.clip((ranks - 1).astype(int), 0, len(rank_means) - 1)
    
    # Vectorized mapping of ranks to mean values
    normalized_data = rank_means[indices]
    
    return pd.DataFrame(normalized_data, index=df.index, columns=df.columns)

def main():
    parser = argparse.ArgumentParser(description='Process gene expression data')
    parser.add_argument('--expression', required=True, help='Expression CSV file')
    parser.add_argument('--fasta', required=True, help='FASTA sequences file')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Validate input files exist
    if not os.path.exists(args.expression):
        raise FileNotFoundError(f"Expression file not found: {args.expression}")
    if not os.path.exists(args.fasta):
        raise FileNotFoundError(f"FASTA file not found: {args.fasta}")
    
    # Read expression data
    try:
        expr_df = pd.read_csv(args.expression, index_col=0)
        print(f"Loaded {len(expr_df)} genes from expression file")
    except Exception as e:
        raise ValueError(f"Error reading expression file: {e}")
    
    if expr_df.empty:
        raise ValueError("Expression file is empty!")
    
    # Parse FASTA
    try:
        seq_lengths = parse_fasta(args.fasta)
        print(f"Loaded {len(seq_lengths)} sequences from FASTA file")
    except Exception as e:
        raise ValueError(f"Error reading FASTA file: {e}")
    
    if not seq_lengths:
        raise ValueError("No sequences found in FASTA file!")
    
    # Find common genes
    common_genes = set(expr_df.index) & set(seq_lengths.keys())
    print(f"Found {len(common_genes)} genes in both files")
    
    if len(common_genes) == 0:
        raise ValueError("No common genes found between expression and FASTA files!")
    
    # Filter to common genes only
    expr_df = expr_df.loc[list(common_genes)]
    
    # Filter genes with mean TPM < 1
    mean_tpm = expr_df.mean(axis=1)
    filtered_df = expr_df[mean_tpm >= 1]
    print(f"After TPM filtering: {len(filtered_df)} genes remain")
    
    if filtered_df.empty:
        raise ValueError("No genes remain after TPM filtering!")
    
    # Calculate stats on filtered data
    filtered_mean_tpm = filtered_df.mean(axis=1)
    filtered_std_tpm = filtered_df.std(axis=1)
    
    # Quantile normalize
    print("Performing quantile normalization...")
    normalized_df = quantile_normalize(filtered_df)
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Save normalized expression
    normalized_df.to_csv(os.path.join(args.output, 'normalized_expression.csv'))
    
    # Create gene stats - using filtered data statistics
    stats_data = []
    for gene in normalized_df.index:
        stats_data.append({
            'gene_name': gene,
            'mean_tpm': filtered_mean_tpm[gene],
            'std_tpm': filtered_std_tpm[gene],
            'seq_length': seq_lengths[gene]
        })
    
    stats_df = pd.DataFrame(stats_data)
    stats_df.to_csv(os.path.join(args.output, 'gene_stats.csv'), index=False)
    
    # Print summary
    if len(stats_df) > 1:  # Need at least 2 points for correlation
        correlation = stats.pearsonr(stats_df['mean_tpm'], stats_df['seq_length'])[0]
        print(f"Samples: {len(expr_df.columns)}")
        print(f"Genes before filter: {len(expr_df)}")
        print(f"Genes after filter: {len(filtered_df)}")
        print(f"Expression-length correlation: {correlation:.3f}")
    else:
        print("Not enough genes for correlation analysis")

if __name__ == '__main__':
    main()
