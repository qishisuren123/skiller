# NumPy Linear Algebra Functions
np.linalg.eigh(a)  # Eigenvalues and eigenvectors of symmetric matrix
np.cov(m, rowvar=True)  # Covariance matrix (set rowvar=False for column variables)
np.mean(a, axis=None)  # Mean along specified axis
np.std(a, axis=None)   # Standard deviation along specified axis
np.argsort(a)[::-1]    # Indices for descending sort

# Pandas DataFrame Operations
df.groupby('column').agg(['mean', 'std'])  # Group statistics
df.dropna()  # Remove rows with NaN values
df.nunique()  # Count unique values per column
df.value_counts()  # Count occurrences of each value

# Mathematical Functions
np.power(base, exponent)  # Element-wise power
np.pi  # Pi constant (3.14159...)
np.sum(a, axis=None)  # Sum along specified axis

# File I/O
pd.read_csv(filepath)  # Read CSV file
df.to_csv(filepath, index=False)  # Write CSV without row indices
json.dump(obj, file, indent=2)  # Write JSON with formatting
