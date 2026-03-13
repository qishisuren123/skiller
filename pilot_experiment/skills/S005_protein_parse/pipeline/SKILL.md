# SwissProt JSON to CSV Parser with Streaming

## Overview
This skill helps create a robust Python CLI script that parses large SwissProt protein entries from JSON format and extracts structured information to CSV, handling memory constraints through streaming and various data structure edge cases.

## Workflow
1. **Set up argument parsing** with input/output file paths
2. **Import required libraries** including ijson for streaming large JSON files
3. **Create parsing function** that handles nested JSON structures safely
4. **Implement streaming JSON processing** to avoid memory issues with large files
5. **Extract key protein information**: accession, names, genes, organism, sequence data, features, GO terms
6. **Handle multiple data formats** for protein names (recommended vs alternative) and gene names (arrays)
7. **Write CSV incrementally** while processing to maintain low memory footprint
8. **Calculate summary statistics** during processing without storing all data
9. **Provide progress feedback** for large file processing

## Common Pitfalls
- **Nested JSON structure assumptions**: SwissProt JSON has deeply nested structures (protein.recommendedName.fullName vs direct access)
- **Missing data causing KeyErrors**: Always use .get() with defaults instead of direct key access
- **ZeroDivisionError in statistics**: Filter out entries with missing data before calculating averages
- **Memory issues with large files**: Standard json.load() loads entire file into memory - use ijson for streaming
- **Multiple data formats**: Gene names are arrays, protein names can be recommended or alternative
- **Incorrect ijson syntax**: Use 'item' path for array elements, not 'items'

## Error Handling
- **Import error handling**: Check for ijson availability and provide installation instructions
- **File access errors**: Use proper file context managers
- **Missing JSON fields**: Use .get() with sensible defaults throughout parsing
- **Empty data validation**: Check for empty lists/dicts before accessing elements
- **Division by zero**: Validate denominators before calculating averages

## Quick Reference
