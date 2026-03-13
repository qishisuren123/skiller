# pandas DataFrame operations
df.mean(axis=1)          # Row-wise means for composite scores
df.var(axis=0, ddof=1)   # Column-wise variance with sample correction
df.between(1, 5)         # Validate Likert range
df.groupby('gender')     # Group analysis by demographics

# argparse for CLI
parser.add_argument('--input', required=True)
parser.add_argument('--reverse-items', default='q3,q5,q7')

# File I/O operations
pd.read_csv(filepath)
df.to_csv(filepath, index=False)
json.dump(data, file, indent=2)
os.makedirs(path, exist_ok=True)

# Cronbach's Alpha Formula
# alpha = (k/(k-1)) * (1 - sum(item_variances) / total_variance)
# where k = number of items
