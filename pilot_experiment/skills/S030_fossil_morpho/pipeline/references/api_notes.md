# pandas DataFrame methods for missing data
df.dropna(subset=['col1', 'col2'])  # Remove rows with NaN in specified columns
df['col'].isna().sum()              # Count NaN values
df['col'].notna().sum()             # Count non-NaN values
series.dropna()                     # Remove NaN from series

# numpy array operations
np.where(condition, value_if_true, value_if_false)  # Conditional assignment
np.linalg.eig(matrix)                               # Eigenvalue decomposition
np.cov(X.T)                                         # Covariance matrix
np.mean(X, axis=0)                                  # Column-wise mean
np.std(X, axis=0)                                   # Column-wise standard deviation

# argparse CLI setup
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--input', required=True, help='...')
args = parser.parse_args()

# File operations
os.makedirs(path, exist_ok=True)    # Create directory if not exists
pd.read_csv(filepath)               # Read CSV file
df.to_csv(filepath, index=False)    # Write CSV file
json.dump(data, file, indent=2)     # Write JSON file
