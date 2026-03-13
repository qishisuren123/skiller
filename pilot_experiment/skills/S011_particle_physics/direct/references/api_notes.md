# pandas DataFrame operations for physics data
df.between(left, right)  # Check if values fall within range (inclusive)
pd.to_numeric(series, errors='coerce')  # Convert to numeric, NaN for invalid
df.dropna(subset=columns)  # Remove rows with NaN in specified columns

# numpy operations for physics calculations
np.abs(array)  # Absolute value for pseudorapidity cuts |eta| < 2.5
np.sqrt(array)  # Square root for significance calculation S/√(S+B)
np.where(condition, x, y)  # Vectorized conditional assignment

# argparse for CLI physics tools
parser.add_argument('--mass-window', default='80,100')  # Physics parameter defaults
parser.add_argument('--input', required=True)  # Required file paths

# JSON for physics analysis summaries
json.dump(dict, file, indent=2)  # Pretty-printed analysis results
