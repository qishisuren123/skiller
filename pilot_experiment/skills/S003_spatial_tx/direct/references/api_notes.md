# pandas - Data manipulation
pd.read_csv(filepath) - Load CSV file into DataFrame
df.columns - Access column names
df[columns] - Select specific columns
df.fillna(value) - Fill missing values
pd.to_numeric(series, errors='coerce') - Convert to numeric with error handling

# numpy - Numerical operations  
np.log1p(x) - Compute log(1 + x) element-wise
np.sum(axis=0/1) - Sum along axis (0=rows, 1=columns)

# DataFrame operations for spatial transcriptomics
df.sum(axis=1) - Sum across genes for each spot (total counts per spot)
df.sum(axis=0) - Sum across spots for each gene (total expression per gene)
df.var(axis=0) - Calculate variance across spots for each gene
(df > 0).sum(axis=0) - Count non-zero values per gene
df.div(series, axis=0) - Divide DataFrame by Series along rows
series.nlargest(n) - Get n largest values from Series

# argparse - Command line interface
parser.add_argument(name, type=int, default=value, help=text)
parser.parse_args() - Parse command line arguments

# pathlib - File path operations
Path(filepath).exists() - Check if file exists
Path(filepath).parent.mkdir(parents=True, exist_ok=True) - Create directories
