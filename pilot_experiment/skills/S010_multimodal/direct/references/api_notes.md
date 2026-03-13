# PIL (Pillow) - Image Processing
Image.open(path) - Load image from file
Image.resize(size, resample=Image.Resampling.LANCZOS) - Resize image with high-quality resampling
Image.convert(mode) - Convert image mode ('RGB', 'RGBA', 'L', etc.)
Image.save(path, format) - Save image in specified format

# Pandas - CSV Processing
pd.read_csv(path) - Load CSV file into DataFrame
df.columns - Access column names
dict(zip(df['col1'], df['col2'])) - Create dictionary from two columns

# Pathlib - Path Operations
Path(path).mkdir(parents=True, exist_ok=True) - Create directory recursively
Path(file).stem - Get filename without extension
Path(file).suffix - Get file extension

# Collections - Data Structures
Counter(iterable) - Count occurrences of elements
Counter.items() - Get (element, count) pairs

# JSON - Data Serialization
json.dump(data, file, indent=2) - Write JSON to file with formatting
json.load(file) - Read JSON from file

# Argparse - CLI Interface
parser.add_argument('--name', required=True, type=int, default=value, help='description')
parser.parse_args() - Parse command line arguments
