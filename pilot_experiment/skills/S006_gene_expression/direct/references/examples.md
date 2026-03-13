# Example 1: Basic quantile normalization
import pandas as pd
import numpy as np

# Sample expression data
data = pd.DataFrame({
    'Gene1': [10, 20, 15],
    'Gene2': [5, 25, 10], 
    'Gene3': [30, 5, 20]
}, index=['Sample1', 'Sample2', 'Sample3'])

def quantile_normalize(df):
    ranks = df.rank(method='average', axis=0)
    sorted_df = df.apply(lambda x: x.sort_values().values, axis=0)
    rank_means = sorted_df.mean(axis=1)
    normalized = ranks.apply(lambda x: rank_means.iloc[x.astype(int) - 1].values, axis=0)
    normalized.index = df.index
    normalized.columns = df.columns
    return normalized

normalized = quantile_normalize(data)
print(normalized)

# Example 2: FASTA parsing with error handling
def robust_fasta_parser(fasta_file):
    sequences = {}
    current_gene = None
    current_seq = []
    
    try:
        with open(fasta_file, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                    
                if line.startswith('>'):
                    # Save previous sequence
                    if current_gene and current_seq:
                        seq_str = ''.join(current_seq)
                        if seq_str:  # Only add non-empty sequences
                            sequences[current_gene] = len(seq_str)
                    
                    # Start new sequence
                    current_gene = line[1:].split()[0]  # Take first word after >
                    current_seq = []
                elif current_gene:  # Only add sequence if we have a gene name
                    # Validate sequence characters
                    clean_seq = ''.join(c for c in line.upper() if c in 'ATCGN')
                    current_seq.append(clean_seq)
                else:
                    print(f"Warning: Sequence data without header at line {line_num}")
            
            # Process last sequence
            if current_gene and current_seq:
                seq_str = ''.join(current_seq)
                if seq_str:
                    sequences[current_gene] = len(seq_str)
                    
    except FileNotFoundError:
        print(f"Error: FASTA file {fasta_file} not found")
        return {}
    except Exception as e:
        print(f"Error parsing FASTA file: {e}")
        return {}
    
    return sequences

# Usage
sequences = robust_fasta_parser('sequences.fasta')
print(f"Parsed {len(sequences)} sequences")
