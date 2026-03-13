# pandas DataFrame operations
df.copy()                    # Create copy to avoid modifying original
df[items].dropna()          # Remove rows with missing values
df[items].mean(axis=1)      # Row-wise mean for composite scores
df[items].corr()            # Correlation matrix
df.to_csv(path, index=False) # Save without row indices

# argparse
parser.add_argument('--name', required=True, help='description')
args = parser.parse_args()   # Returns namespace object
# Note: --reverse-items becomes args.reverse_items

# pathlib
Path(directory).mkdir(parents=True, exist_ok=True)  # Create directory structure

# numpy
np.nan                       # Not a number for invalid calculations
np.trace(matrix)            # Sum of diagonal elements
