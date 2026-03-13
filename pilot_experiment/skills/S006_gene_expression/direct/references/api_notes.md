# pandas - Data manipulation
pd.read_csv(filepath, index_col=0)  # Load CSV with row names
df.mean(axis=0)  # Calculate mean across rows (per column)
df.rank(method='average', axis=0)  # Rank values within columns
df.dropna(subset=['column'])  # Remove rows with NaN in specific columns

# numpy - Numerical operations  
np.nan  # Not-a-number value for missing data
np.corrcoef(x, y)  # Correlation coefficient between arrays

# scipy.stats - Statistical functions
stats.pearsonr(x, y)  # Pearson correlation coefficient and p-value
stats.rankdata(array, method='average')  # Rank data with tie handling

# pathlib - File system operations
Path(directory).mkdir(parents=True, exist_ok=True)  # Create directory structure
Path(dir) / 'filename.csv'  # Cross-platform path joining

# argparse - Command line parsing
parser.add_argument('--name', required=True, help='Description')
args = parser.parse_args()  # Parse command line arguments
