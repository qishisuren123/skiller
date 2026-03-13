# argparse - Command line argument parsing
parser = argparse.ArgumentParser(description='Description')
parser.add_argument('--input', required=True, help='Help text')
parser.add_argument('--min-quality', type=int, default=20, help='Help text')
args = parser.parse_args()

# collections.defaultdict - Dictionary with default values
from collections import defaultdict
quality_dist = defaultdict(int)  # Missing keys default to 0
quality_dist[score] += 1

# json - JSON file handling
import json
with open(filename, 'w') as f:
    json.dump(data_dict, f, indent=2)

# File I/O - Reading and writing files
with open(filename, 'r') as f:
    line = f.readline().strip()  # Read one line, remove whitespace
    
with open(filename, 'w') as f:
    f.write(f"{header}\n{sequence}\n+\n{quality}\n")

# ord() - Convert character to ASCII value
phred_score = ord(quality_char) - 33  # FASTQ quality offset
