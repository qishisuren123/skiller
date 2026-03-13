# Example 1: Basic usage with minimal spatial transcriptomics data
"""
Input CSV format:
spot_id,x,y,Gene1,Gene2,Gene3,Gene4
spot_001,100,200,5,0,12,3
spot_002,101,200,0,8,15,0
spot_003,102,200,2,1,0,7

Command line usage:
python main.py --input spatial_data.csv --output processed_data.csv --n-top-genes 3
"""

# Example 2: Processing workflow demonstration
import pandas as pd
import numpy as np

# Sample data processing steps
def example_processing():
    # Load sample data
    data = {
        'spot_id': ['spot_001', 'spot_002', 'spot_003'],
        'x': [100, 101, 102],
        'y': [200, 200, 200],
        'Gene1': [5, 0, 2],
        'Gene2': [0, 8, 1], 
        'Gene3': [12, 15, 0],
        'Gene4': [3, 0, 7]
    }
    df = pd.DataFrame(data)
    
    # Separate counts and metadata
    metadata_cols = ['spot_id', 'x', 'y']
    count_cols = ['Gene1', 'Gene2', 'Gene3', 'Gene4']
    counts = df[count_cols].copy()
    counts.index = df['spot_id']
    
    # Filter genes (expressed in >= 3 spots)
    gene_spot_counts = (counts > 0).sum(axis=0)
    valid_genes = gene_spot_counts >= 2  # Relaxed for small example
    filtered_counts = counts.loc[:, valid_genes]
    
    # Normalize to 10000 and log transform
    spot_totals = filtered_counts.sum(axis=1)
    normalized = filtered_counts.div(spot_totals, axis=0) * 10000
    log_transformed = np.log1p(normalized)
    
    # Select top HVGs
    gene_vars = log_transformed.var(axis=0)
    top_genes = gene_vars.nlargest(2).index
    final_matrix = log_transformed[top_genes]
    
    print("Final processed matrix:")
    print(final_matrix)
    print(f"\nGene variances: {gene_vars.sort_values(ascending=False)}")

# example_processing()
