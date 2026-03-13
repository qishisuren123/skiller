# SKILL: SwissProt JSON to CSV Parser

## Overview
This tool parses SwissProt protein entries from a JSON file and extracts structured biological data into a CSV format. It handles missing fields gracefully and generates summary statistics about the dataset.

## Step-by-Step Workflow

1. **Parse Command-Line Arguments**
   - Use `argparse` to accept `--input` (JSON file path) and `--output` (CSV file path)
   - Validate that input file exists before processing

2. **Load JSON Data**
   - Read the JSON file and parse it into a list of protein entry dictionaries
   - Handle JSON parsing errors with informative error messages

3. **Initialize Output Structure**
   - Create a list to store extracted records
   - Prepare tracking variables for summary statistics (organism set, sequence lengths)

4. **Iterate and Extract Data**
   - Loop through each protein entry
   - For each entry, extract: accession, protein_name, gene_name, organism, sequence_length, feature_count, GO_terms
   - Use `.get()` method with defaults for missing fields

5. **Extract GO Terms**
   - Search `dbReferences` array for entries with `type: "GO"`
   - Collect all GO IDs; join with semicolon if multiple exist
   - Return empty string if no GO terms found

6. **Write CSV Output**
   - Use `csv.DictWriter` to write headers and rows
   - Ensure all fields are present in each row (use empty strings for missing data)

7. **Print Summary Statistics**
   - Calculate and display: total protein count, unique organism count, average sequence length
   - Format output for readability

## Common Pitfalls & Solutions

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Missing nested fields** | KeyError when accessing `protein.recommendedName.fullName` | Use safe navigation: `entry.get('protein', {}).get('recommendedName', {}).get('fullName', '')` |
| **Malformed JSON** | Script crashes on invalid JSON syntax | Wrap JSON loading in try-except; print line number and context of error |
| **Empty or None sequences** | Sequence length calculation fails on None values | Check `if sequence` before calling `len()`; default to 0 |
| **Large files in memory** | Memory overflow with huge JSON files | Consider streaming with `ijson` library for very large datasets |
| **Inconsistent GO term structure** | GO terms nested differently across entries | Validate `dbReferences` is a list; check each item has `type` and `id` keys |

## Error Handling Tips

- **File I/O**: Wrap file operations in try-except blocks; catch `FileNotFoundError`, `IOError`, `PermissionError`
- **JSON Parsing**: Catch `json.JSONDecodeError` with line/column info for debugging
- **CSV Writing**: Ensure output directory exists; handle `IOError` if disk is full
- **Data Validation**: Log warnings (not errors) for missing optional fields; continue processing
- **Graceful Degradation**: Use sensible defaults (empty string, 0, empty list) rather than failing on missing data

## Reference Code Snippet

```python
import json
import csv
import argparse
from collections import defaultdict

def extract_go_terms(db_references):
    """Extract GO term IDs from dbReferences array."""
    if not db_references:
        return ""
    go_terms = [ref.get('id', '') for ref in db_references 
                if ref.get('type') == 'GO']
    return ";".join(go_terms)

def parse_protein_entry(entry):
    """Extract structured data from a single protein entry."""
    return {
        'accession': entry.get('accession', ''),
        'protein_name': entry.get('protein', {}).get('recommendedName', {}).get('fullName', ''),
        'gene_name': entry.get('gene', [{}])[0].get('name', {}).get('value', '') if entry.get('gene') else '',
        'organism': entry.get('organism', {}).get('name', ''),
        'sequence_length': len(entry.get('sequence', '')) if entry.get('sequence') else 0,
        'number_of_features': len(entry.get('features', [])),
        'GO_terms': extract_go_terms(entry.get('dbReferences', []))
    }

def main():
    parser = argparse.ArgumentParser(description='Parse SwissProt JSON to CSV')
    parser.add_argument('--input', required=True, help='Input JSON file path')
    parser.add_argument('--output', required=True, help='Output CSV file path')
    args = parser.parse_args()
    
    try:
        with open(args.input, 'r') as f:
            entries = json.load(f)
    except json.JSONDecodeError as e:
        print(f"JSON Error: {e}")
        return
    
    records = []
    organisms = set()
    seq_lengths = []
    
    for entry in entries:
        record = parse_protein_entry(entry)
        records.append(record)
        organisms.add(record['organism'])
        if record['sequence_length'] > 0:
            seq_lengths.append(record['sequence_length'])
    
    with open(args.output, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    
    avg_length = sum(seq_lengths) / len(seq_lengths) if seq_lengths else 0
    print(f"Total proteins: {len(records)}")
    print(f"Unique organisms: {len(organisms)}")
    print(f"Average sequence length: {avg_length:.1f}")

if __name__ == '__main__':
    main()
```