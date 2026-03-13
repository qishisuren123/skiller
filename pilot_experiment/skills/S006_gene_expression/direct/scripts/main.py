#!/usr/bin/env python3
import argparse
import pandas as pd
import numpy as np
from scipy import stats
import os
from pathlib import Path

def parse_fasta(fasta_file):
    """Parse FASTA file and return dictionary of gene names to sequence lengths."""
    sequences = {}
    current_gene = None
    current_seq = []
    
    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                # Save previous sequence if exists
                if current_gene and current_seq:
                    sequences[current_gene] = len(''.join(current_seq))
                # Start new sequence
                current_gene = line[1:]  # Remove '>' character
                current_seq = []
            else:
                current_seq.append(line)
        
        # Don't forget the last sequence
        if current_gene and current_seq:
            sequences[current_gene] = len(''.join(current_seq))
    
    return sequences

def quantile_normalize(df):
    """Apply quantile normalization across samples (columns)."""
    # Get the rank of each value within each sample
    ranks = df.rank(method='average', axis=0)
    
    # Calculate mean expression at each rank across all samples
    sorted_df = df.apply(lambda x: x.sort_values().values, axis=0)
    rank_means = sorted_df.mean(axis=1)
    
    # Map ranks back to normalized values
    normalized = ranks.apply(lambda x: rank_means.iloc[x.astype(int) - 1].values, axis=0)
    normalized.index = df.index
    normalized.columns = df.columns
    
    return normalized

def main():
    parser = argparse.ArgumentParser(description='Process gene expression data with sequence information')
    parser.add_argument('--expression', required=True, help='Expression CSV file (samples as rows, genes as columns)')
    parser.add_argument('--fasta', required=True, help='FASTA file with gene sequences')
    parser.add_argument('--output', required=True, help='Output directory')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load expression data
    print("Loading expression data...")
    expr_df = pd.read_csv(args.expression, index_col=0)
    print(f"Loaded expression data: {expr_df.shape[0]} samples, {expr_df.shape[1]} genes")
    
    # Filter genes with mean TPM < 1
    print("Filtering genes by expression level...")
    gene_means = expr_df.mean(axis=0)
    filtered_genes = gene_means[gene_means >= 1.0].index
    expr_filtered = expr_df[filtered_genes]
    print(f"After filtering: {len(filtered_genes)} genes remain")
    
    # Quantile normalize
    print("Applying quantile normalization...")
    expr_normalized = quantile_normalize(expr_filtered)
    
    # Parse FASTA sequences
    print("Parsing FASTA sequences...")
    sequences = parse_fasta(args.fasta)
    print(f"Parsed {len(sequences)} sequences from FASTA")
    
    # Calculate gene statistics
    print("Calculating gene statistics...")
    gene_stats = []
    matched_genes = 0
    
    for gene in expr_normalized.columns:
        mean_tpm = expr_filtered[gene].mean()
        std_tpm = expr_filtered[gene].std()
        
        # Try to find matching sequence
        seq_length = None
        if gene in sequences:
            seq_length = sequences[gene]
            matched_genes += 1
        else:
            # Try alternative matching strategies
            for seq_name in sequences:
                if gene in seq_name or seq_name in gene:
                    seq_length = sequences[seq_name]
                    matched_genes += 1
                    break
        
        gene_stats.append({
            'gene_name': gene,
            'mean_tpm': mean_tpm,
            'std_tpm': std_tpm,
            'seq_length': seq_length
        })
    
    gene_stats_df = pd.DataFrame(gene_stats)
    
    # Save outputs
    print("Saving results...")
    expr_normalized.to_csv(output_dir / 'normalized_expression.csv')
    gene_stats_df.to_csv(output_dir / 'gene_stats.csv', index=False)
    
    # Calculate correlation between expression and sequence length
    stats_with_length = gene_stats_df.dropna(subset=['seq_length'])
    correlation = np.nan
    p_value = np.nan
    
    if len(stats_with_length) > 2:
        correlation, p_value = stats.pearsonr(stats_with_length['mean_tpm'], 
                                            stats_with_length['seq_length'])
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Samples processed: {expr_df.shape[0]}")
    print(f"Genes before filtering: {expr_df.shape[1]}")
    print(f"Genes after filtering: {len(filtered_genes)}")
    print(f"Genes with sequence data: {matched_genes}")
    print(f"Expression-length correlation: {correlation:.4f} (p={p_value:.4f})")
    print(f"Results saved to: {output_dir}")

if __name__ == "__main__":
    main()
