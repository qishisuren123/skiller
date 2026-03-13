# pandas DataFrame operations
df = pd.read_csv(filename, index_col=0)  # Read CSV with first column as index
df.to_csv(filename, index=False)         # Write CSV without row indices
(df > 0).any().sum()                     # Count columns with any positive values
df.select_dtypes(exclude=[np.number])    # Get non-numeric columns
df.index[(df == 0).all(axis=1)]         # Get row indices where all values are 0

# argparse for CLI
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--input', required=True, help='...')
parser.add_argument('--indices', default='all', help='...')

# Mathematical calculations
math.log(x)     # Natural logarithm
sum(iterable)   # Sum of values
max(0, x)       # Ensure non-negative values
