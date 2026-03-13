# SwissProt JSON to CSV Parser

## Overview
A Python CLI tool that parses SwissProt protein entries from JSON format and extracts key structured information into a CSV file. The tool handles missing fields gracefully and provides summary statistics about the processed proteins.

## Workflow

1. **Parse command line arguments** using argparse to get input JSON and output CSV paths
2. **Load and validate JSON file** containing protein entries list
3. **Initialize data structures** for tracking extracted data and statistics
4. **Iterate through each protein entry** and extract required fields:
   - accession, protein_name, gene_name, organism, sequence_length, number_of_features, GO_terms
5. **Handle missing fields** by applying default values (empty strings or 0)
6. **Write extracted data to CSV** with proper headers and formatting
7. **Generate and display summary statistics** (total proteins, organism count, average sequence length)

## Common Pitfalls & Solutions

1. **Nested field access errors**
   - *Problem*: Fields like `protein.recommendedName.fullName` may not exist
   - *Solution*: Use `.get()` method with chaining or try-except blocks

2. **GO terms extraction complexity**
   - *Problem*: GO terms are buried in `dbReferences` array with specific type filtering
   - *Solution*: Filter `dbReferences` by type "GO" first, then extract properties

3. **Sequence length calculation**
   - *Problem*: Sequence field might be missing or contain non-string data
   - *Solution*: Check if sequence exists and is string before calling `len()`

4. **CSV encoding issues**
   - *Problem*: Protein names may contain special characters causing encoding errors
   - *Solution*: Open CSV file with `encoding='utf-8'` parameter

5. **Empty input file handling**
   - *Problem*: JSON file might be empty or contain empty list
   - *Solution*: Check if data exists before processing and handle gracefully

## Error Handling Tips

- Wrap JSON loading in try-except to catch malformed JSON files
- Use `.get()` method for dictionary access with sensible defaults
- Validate file paths exist before processing
- Handle division by zero when calculating average sequence length
- Log warnings for entries with missing critical fields rather than failing completely

## Reference Code Snippet

```python
def extract_protein_data(protein_entry):
    """Extract structured data from a single protein entry"""
    try:
        # Basic fields with safe access
        accession = protein_entry.get('accession', '')
        protein_name = protein_entry.get('protein', {}).get('recommendedName', {}).get('fullName', '')
        gene_name = protein_entry.get('gene', [{}])[0].get('name', '') if protein_entry.get('gene') else ''
        organism = protein_entry.get('organism', {}).get('scientificName', '')
        
        # Sequence length calculation
        sequence = protein_entry.get('sequence', '')
        sequence_length = len(sequence) if isinstance(sequence, str) else 0
        
        # Features count
        features = protein_entry.get('features', [])
        number_of_features = len(features) if isinstance(features, list) else 0
        
        # GO terms extraction
        go_terms = []
        db_refs = protein_entry.get('dbReferences', [])
        for ref in db_refs:
            if ref.get('type') == 'GO':
                go_terms.append(ref.get('id', ''))
        go_terms_str = ';'.join(go_terms)
        
        return {
            'accession': accession,
            'protein_name': protein_name,
            'gene_name': gene_name,
            'organism': organism,
            'sequence_length': sequence_length,
            'number_of_features': number_of_features,
            'GO_terms': go_terms_str
        }
    except Exception as e:
        print(f"Warning: Error processing protein entry: {e}")
        return None
```