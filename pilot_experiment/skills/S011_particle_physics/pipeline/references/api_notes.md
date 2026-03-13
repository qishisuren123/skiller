# Pandas DataFrame Operations
- `pd.read_csv(file, dtype=dict)` - Load CSV with specific data types for memory efficiency
- `df.isnull().sum()` - Count NaN values per column
- `df.dropna(subset=columns)` - Remove rows with NaN in specific columns
- `df[boolean_mask]` - Filter DataFrame using boolean indexing
- `df.loc[mask, column] = value` - Set values for specific rows/columns
- `df.copy()` - Create explicit copy to avoid SettingWithCopyWarning

# Argparse
- `parser.add_argument('--flag', required=True, help='description')` - Add command line arguments
- `parser.parse_args()` - Parse command line arguments

# File Operations
- `os.path.exists(path)` - Check if file exists
- `os.makedirs(path, exist_ok=True)` - Create directory structure
- `os.path.join(dir, filename)` - Platform-independent path joining

# JSON Operations
- `json.dump(data, file, indent=2)` - Write formatted JSON to file
