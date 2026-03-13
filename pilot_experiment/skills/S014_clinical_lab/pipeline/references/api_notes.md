# CSV Module
csv.DictReader(file) - Read CSV with headers as dictionary keys
csv.DictWriter(file, fieldnames) - Write CSV with dictionary rows
writer.writeheader() - Write header row
writer.writerows(data) - Write multiple data rows

# JSON Module  
json.dump(data, file, indent=2) - Write formatted JSON to file

# DateTime Module
datetime.strptime(string, format) - Parse string to datetime object
Common formats: '%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y'

# Argparse Module
parser.add_argument('--flag', required=True, help='Description')
args = parser.parse_args() - Parse command line arguments

# String Methods
str.strip() - Remove leading/trailing whitespace
str.lower() - Convert to lowercase for comparison
