# pandas DataFrame operations
df.columns.duplicated()  # Check for duplicate column names
df.loc[:, ~df.columns.duplicated()]  # Remove duplicate columns
df.fillna(0)  # Fill missing values
df.where(condition, replacement)  # Conditional replacement
pd.to_numeric(series, errors='coerce')  # Convert to numeric with error handling
df.div(series, axis=0)  # Element-wise division along axis
df.sum(axis=1)  # Sum along rows (spots)
df.sum(axis=0)  # Sum along columns (genes)
df.var(axis=0)  # Calculate variance along columns
series.nlargest(n)  # Get n largest values
df.to_csv(path, index_label='name')  # Save with named index

# numpy operations
np.log1p(array)  # Log(1 + x) transformation

# argparse
parser.add_argument('--flag', required=True, help='description')
parser.add_argument('--number', type=int, default=value)
