# SwissProt JSON Parser

## Overview
This skill helps parse SwissProt protein database entries from JSON format and extract structured biological information into CSV format with comprehensive error handling for missing fields.

## Workflow
1. Set up argparse to handle input JSON file and output CSV file paths
2. Load and validate the JSON file structure containing protein entries
3. Initialize data extraction with proper field mapping for SwissProt schema
4. Iterate through each protein entry and extract: accession, protein_name, gene_name, organism, sequence_length, number_of_features, and GO_terms
5. Handle missing or malformed fields by applying default values (empty strings for text, 0 for counts)
6. Write extracted data to CSV using pandas DataFrame for proper formatting
7. Generate and print summary statistics including total proteins, unique organisms, and average sequence length

## Common Pitfalls
- **Nested field access errors**: SwissProt JSON has deeply nested structures (protein.recommendedName.fullName). Use safe dictionary access with .get() method and handle None values
- **Multiple gene names**: Gene field can contain multiple names or be missing. Extract the first primary gene name or use empty string as fallback
- **GO term extraction complexity**: dbReferences contains mixed reference types. Filter specifically for "GO" type references and extract only the ID field
- **Sequence length calculation**: Sequence field might be missing or contain non-standard characters. Use len() with proper None checking
- **CSV encoding issues**: Protein names may contain special characters. Use UTF-8 encoding when writing CSV files

## Error Handling
- Wrap JSON loading in try-except to catch malformed files and provide clear error messages
- Use safe dictionary navigation with nested .get() calls to prevent KeyError exceptions
- Validate that required output directory exists before writing CSV file
- Handle empty input files gracefully and report zero-entry summary statistics

## Quick Reference
