# pandas DataFrame operations
df.rank(method='average')  # Handle ties by averaging ranks
df.mean(axis=1)           # Calculate mean across columns (samples)
df.std(axis=1)            # Calculate standard deviation across columns
df.loc[gene_list]         # Filter DataFrame to specific genes

# numpy array operations
np.sort(data, axis=0)     # Sort along gene axis (each sample independently)
np.mean(sorted_data, axis=1)  # Mean across samples for each rank position
np.clip(indices, 0, max_val)  # Clip indices to valid range

# scipy.stats
stats.pearsonr(x, y)[0]   # Pearson correlation coefficient

# argparse
parser.add_argument('--flag', required=True, help='Description')
args = parser.parse_args()

# File operations
os.path.exists(filepath)  # Check if file exists
os.makedirs(path, exist_ok=True)  # Create directory if doesn't exist
