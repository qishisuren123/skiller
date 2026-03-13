# Key Libraries for SwissProt JSON Parsing

## pandas
- `pd.DataFrame(data)` - Create DataFrame from list of dictionaries
- `df.to_csv(filename, index=False, encoding='utf-8')` - Export to CSV with proper encoding
- `df['column'].nunique()` - Count unique values in column
- `df['column'].mean()` - Calculate mean of numeric column

## json
- `json.load(file_object)` - Load JSON from file handle
- Handle JSONDecodeError for malformed files

## argparse
- `ArgumentParser(description='...')` - Create CLI parser
- `add_argument('--flag', required=True, help='...')` - Add required arguments
- `parse_args()` - Parse command line arguments

## pathlib.Path
- `Path(filename).parent.mkdir(parents=True, exist_ok=True)` - Create output directories
- Better path handling than os.path for cross-platform compatibility

## Dictionary Navigation
- `dict.get(key, default)` - Safe key access with fallback
- Handle nested structures with multiple .get() calls
- Check isinstance() before accessing list/dict methods
