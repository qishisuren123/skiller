# Duplicate column handling
if data.columns.duplicated().any():
    data = data.loc[:, ~data.columns.duplicated()]

# Safe boolean filtering with metadata alignment
valid_spots = spot_totals > 0
count_matrix = count_matrix.loc[valid_spots]
metadata = metadata.loc[valid_spots]

# Data cleaning pipeline
count_matrix = count_matrix.fillna(0)  # Handle NaN
count_matrix = count_matrix.where(count_matrix >= 0, 0)  # Handle negatives
count_matrix = count_matrix.apply(pd.to_numeric, errors='coerce').fillna(0)

# Normalization with division by zero protection
spot_totals = count_matrix.sum(axis=1)
valid_spots = spot_totals > 0  # Filter before normalization
normalized = count_matrix.div(spot_totals, axis=0) * 10000

# Zero variance gene filtering
gene_vars = log_matrix.var(axis=0)
variable_genes = gene_vars > 0
gene_vars = gene_vars[variable_genes]
log_matrix = log_matrix.loc[:, variable_genes]
