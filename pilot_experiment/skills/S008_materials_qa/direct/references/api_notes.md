# Key Python Standard Library Functions

## argparse.ArgumentParser
- ArgumentParser(description='...'): Create CLI parser
- add_argument('--flag', required=True, help='...'): Add command line arguments
- parse_args(): Parse command line arguments

## json module
- json.loads(string): Parse JSON string to Python object
- json.dump(obj, file, indent=2, ensure_ascii=False): Write JSON to file
- json.dumps(obj, ensure_ascii=False): Convert object to JSON string
- JSONDecodeError: Exception for malformed JSON

## collections module
- Counter(): Dictionary subclass for counting hashable objects
- defaultdict(type): Dictionary with default values for missing keys
- Counter.update(): Add counts from another counter

## File I/O
- open(path, 'r', encoding='utf-8'): Open file for reading with UTF-8 encoding
- open(path, 'w', encoding='utf-8'): Open file for writing with UTF-8 encoding
- file.readline(): Read single line from file
- enumerate(iterable, start=1): Add line numbers to iteration

## String Operations
- str.strip(): Remove leading/trailing whitespace
- str.lower(): Convert to lowercase
- str.split(): Split string into words
- len(string): Get string length
