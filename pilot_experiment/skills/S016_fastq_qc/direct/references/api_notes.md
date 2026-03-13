# Key Python Standard Library Functions for FASTQ Processing

## argparse
- ArgumentParser(): Create command-line argument parser
- add_argument(name, type=int, default=value, help=string): Define CLI arguments
- parse_args(): Parse command-line arguments into namespace object

## File I/O
- open(filename, 'r'/'w'): Open file for reading/writing
- readline().strip(): Read single line and remove whitespace
- write(string): Write string to file

## String/Character Operations
- ord(character): Get ASCII value of character
- startswith(prefix): Check if string starts with prefix
- strip(): Remove leading/trailing whitespace

## JSON Operations
- json.dump(data, file, indent=2): Write JSON data to file with formatting

## Collections
- Counter(iterable): Count occurrences of elements
- counter.get(key, default): Get count with default value
