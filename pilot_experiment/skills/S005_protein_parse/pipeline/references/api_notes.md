# ijson - Streaming JSON parser
ijson.items(file, path) - Parse array items from JSON stream
- file: opened in binary mode ('rb')
- path: 'item' for top-level array elements

# argparse - Command line argument parsing
parser.add_argument('--input', required=True, help='description')

# csv.DictWriter - CSV writing with headers
writer = csv.DictWriter(csvfile, fieldnames=list)
writer.writeheader()
writer.writerow(dict)

# Safe dictionary access patterns
dict.get(key, default_value)
dict.get('nested', {}).get('key', default)
