# Materials Science Dataset Validation and Cleaning

## Overview
This skill helps validate, clean, and deduplicate materials science training datasets stored in JSONL format, ensuring data quality for machine learning applications by checking field completeness, enforcing length constraints, detecting near-duplicates, and generating comprehensive quality reports.

## Workflow
1. **Parse command line arguments** using argparse to get input JSONL path, output cleaned path, and report JSON path
2. **Load and validate JSONL entries** by checking required fields (instruction, input, output, source, category) and enforcing length limits
3. **Detect near-duplicates** using word overlap ratio calculation between instruction fields with 0.9 similarity threshold
4. **Filter and clean dataset** by removing invalid entries and duplicate instructions while tracking removal reasons
5. **Calculate dataset statistics** including category distribution, average field lengths, and removal counts by reason
6. **Write cleaned JSONL output** with valid, deduplicated entries in the same format
7. **Generate comprehensive report** as JSON with validation metrics, statistics, and data quality insights

## Common Pitfalls
- **Malformed JSON lines**: Use try-except blocks around json.loads() to handle corrupted entries gracefully and log specific line numbers
- **Memory issues with large datasets**: Process JSONL line-by-line rather than loading entire file into memory, especially for duplicate detection
- **Unicode encoding problems**: Always open files with explicit UTF-8 encoding to handle international characters in materials science terminology
- **Case sensitivity in duplicate detection**: Normalize instruction text to lowercase and strip whitespace before similarity comparison
- **Empty or whitespace-only fields**: Check for both None values and strings that are empty after stripping whitespace

## Error Handling
Handle file I/O errors with informative messages about missing input files or write permission issues. Catch JSON parsing errors per line and continue processing while logging problematic entries. Validate data types for all fields and provide specific error messages. Use logging module to track validation issues and processing statistics for debugging.

## Quick Reference
