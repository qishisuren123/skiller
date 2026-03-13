# SKILL: SwissProt JSON to CSV Parser

## Overview
A Python CLI tool that parses SwissProt protein entries from JSON format and extracts key biological information into a structured CSV file. The tool handles complex nested JSON structures, extracts specific protein attributes, and provides summary statistics about the processed dataset.

## Step-by-Step Workflow

1. **Parse Command Line Arguments**
   - Set up argparse with `--input` (JSON file path) and `--output` (CSV file path)
   - Validate that input file exists and is readable

2. **Load and Validate JSON Data**
   - Read JSON file and parse into Python data structure
   - Verify the JSON contains a list/array of protein entries

3. **Extract Protein Information**
   - For each entry, safely extract: accession, protein_name, gene_name, organism, sequence_length
   - Count features in the 'features' array
   - Extract GO terms from dbReferences where database="GO"

4. **Handle Missing/Nested Fields**
   - Use dict.get() with default values for missing fields
   - Navigate nested structures safely (e.g., protein.recommendedName.fullName.value)

5. **Write CSV Output**
   - Create CSV with headers: accession, protein_name, gene_name, organism, sequence_length, number_of_features, GO_terms
   - Write one row per protein entry

6. **Calculate Summary Statistics**
   - Count total proteins processed
   - Count unique organisms
   - Calculate average sequence length

7. **Display Results**
   - Print summary statistics to console
   - Confirm successful file creation

## Common Pitfalls and Solutions

1. **Nested Field Access**
   - *Pitfall*: Accessing `protein.recommendedName.fullName.value` directly causes KeyError
   - *Solution*: Use nested get() calls or try-except blocks

2. **Multiple Gene Names**
   - *Pitfall*: Gene field may contain a list of gene objects
   - *Solution*: Extract primary gene name (first item) or concatenate all

3. **GO Terms Extraction**
   - *Pitfall*: dbReferences is a list with mixed database types
   - *Solution*: Filter for entries where `database == "GO"` and extract IDs

4. **Memory Issues with Large Files**
   - *Pitfall*: Loading entire JSON into memory fails for large datasets
   - *Solution*: Consider streaming JSON parser (ijson) for files >1GB

5. **Encoding Issues**
   - *Pitfall*: Special characters in organism names cause CSV write errors
   - *Solution*: Open output file with `encoding='utf-8'`

## Error Handling Tips

- Wrap JSON loading in try-except to catch `JSONDecodeError`
- Use `if os.path.exists()` before file operations
- Implement graceful degradation for missing fields (don't skip entire entry)
- Add logging for skipped/problematic entries
- Validate CSV write permissions before processing
- Consider using `csv.DictWriter` for more robust CSV handling

## Reference Code Snippet

```python
def extract_protein_info(entry):
    """Extract key information from a protein entry."""
    info = {
        'accession': entry.get('accession', ''),
        'protein_name': '',
        'gene_name': '',
        'organism': '',
        'sequence_length': 0,
        'number_of_features': 0,
        'GO_terms': ''
    }
    
    # Extract protein name (nested structure)
    try:
        protein = entry.get('protein', {})
        rec_name = protein.get('recommendedName', {})
        full_name = rec_name.get('fullName', {})
        info['protein_name'] = full_name.get('value', '')
    except:
        pass
    
    # Extract gene name (may be list)
    gene_data = entry.get('gene', [])
    if isinstance(gene_data, list) and gene_data:
        info['gene_name'] = gene_data[0].get('name', {}).get('value', '')
    
    # Extract organism
    organism = entry.get('organism', {})
    info['organism'] = organism.get('scientificName', '')
    
    # Calculate sequence length
    sequence = entry.get('sequence', {})
    info['sequence_length'] = sequence.get('length', 0)
    
    # Count features
    features = entry.get('features', [])
    info['number_of_features'] = len(features)
    
    # Extract GO terms
    db_refs = entry.get('dbReferences', [])
    go_terms = [ref['id'] for ref in db_refs if ref.get('database') == 'GO']
    info['GO_terms'] = ';'.join(go_terms)
    
    return info
```