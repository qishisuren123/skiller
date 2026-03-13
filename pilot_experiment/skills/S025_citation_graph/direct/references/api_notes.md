# pandas DataFrame operations
pd.read_csv(filepath) - Load CSV file into DataFrame
df.drop_duplicates(subset=['col1', 'col2']) - Remove duplicate rows
df.set_index('column').to_dict('index') - Convert DataFrame to nested dict
df.to_csv(filepath, index=False) - Save DataFrame to CSV

# collections utilities
Counter(iterable) - Count occurrences of elements
Counter.most_common(n) - Get n most frequent elements
defaultdict(set) - Dictionary with default empty sets

# numpy operations
np.mean(array) - Calculate arithmetic mean of array values

# json operations
json.dump(obj, file, indent=2) - Write JSON object to file with formatting

# argparse CLI setup
parser.add_argument('--flag', required=True, help='description')
args = parser.parse_args() - Parse command line arguments

# os file operations
os.makedirs(path, exist_ok=True) - Create directory if doesn't exist
os.path.join(dir, filename) - Platform-independent path joining
