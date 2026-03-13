# FASTA parsing with memory efficiency
def parse_fasta(fasta_file):
    sequences = {}
    current_gene = None
    current_seq_length = 0
    with open(fasta_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('>'):
                if current_gene:
                    sequences[current_gene] = current_seq_length
                current_gene = line[1:].strip()
                current_seq_length = 0
            else:
                current_seq_length += len(line)
        if current_gene:  # Handle last sequence
            sequences[current_gene] = current_seq_length
    return sequences

# Vectorized quantile normalization
def quantile_normalize(df):
    data = df.values.copy()
    sorted_data = np.sort(data, axis=0)
    rank_means = np.mean(sorted_data, axis=1)
    ranks = df.rank(method='average').values
    indices = np.clip((ranks - 1).astype(int), 0, len(rank_means) - 1)
    normalized_data = rank_means[indices]
    return pd.DataFrame(normalized_data, index=df.index, columns=df.columns)

# Gene filtering and validation
common_genes = set(expr_df.index) & set(seq_lengths.keys())
if len(common_genes) == 0:
    raise ValueError("No common genes found!")
expr_df = expr_df.loc[list(common_genes)]

# Statistics calculation from filtered data
filtered_mean_tpm = filtered_df.mean(axis=1)
filtered_std_tpm = filtered_df.std(axis=1)
