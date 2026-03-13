# argparse - CLI argument parsing
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--input', required=True, help='...')
parser.add_argument('--sample-size', type=int, default=50, help='...')

# json - JSON handling
json.loads(line.strip())  # Parse JSON line
json.dumps(entry)  # Serialize to JSON
json.dump(report, f, indent=2)  # Pretty print to file

# collections - Data structures
defaultdict(int)  # Auto-initializing dict
Counter(items)  # Count occurrences

# re - Regular expressions
re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
re.sub(r'\s+', ' ', text)  # Normalize whitespace
