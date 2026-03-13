# SKILL: Materials Science Dataset Validator & Cleaner

## Overview
A Python CLI tool that validates, deduplicates, and cleans materials science training datasets in JSONL format. The tool checks required fields, enforces length limits, detects near-duplicates using word overlap similarity, and generates comprehensive cleaning reports.

## Workflow

1. **Parse Arguments**: Set up argparse with input JSONL, output JSONL, and report JSON paths
2. **Load & Parse Data**: Read JSONL file line-by-line, parse each JSON entry with error handling
3. **Validate Entries**: Check required fields presence, non-empty instruction/output, and length constraints
4. **Detect Duplicates**: Calculate word overlap ratios between instructions to find near-duplicates (>0.9 similarity)
5. **Filter Dataset**: Remove invalid entries and duplicates, keeping first occurrence of duplicates
6. **Generate Statistics**: Calculate removal counts by reason, category distribution, and average field lengths
7. **Write Outputs**: Save cleaned JSONL and comprehensive report JSON

## Common Pitfalls & Solutions

1. **Memory Issues with Large Files**
   - *Problem*: Loading entire dataset into memory
   - *Solution*: Process entries in streaming fashion, only store necessary data for duplicate detection

2. **JSON Parsing Errors**
   - *Problem*: Malformed JSON lines crash the script
   - *Solution*: Wrap `json.loads()` in try-except, log line numbers of invalid JSON

3. **Inefficient Duplicate Detection**
   - *Problem*: O(n²) comparison of all instruction pairs
   - *Solution*: Use set-based word overlap calculation and early termination for dissimilar lengths

4. **Unicode/Encoding Issues**
   - *Problem*: Special characters in materials science terms cause encoding errors
   - *Solution*: Open files with `encoding='utf-8'` and handle decode errors gracefully

5. **Empty Output File on Errors**
   - *Problem*: Script crashes before writing any valid entries
   - *Solution*: Validate input file exists and is readable before processing

## Error Handling Tips

- Use `try-except` blocks around JSON parsing with specific error messages including line numbers
- Validate file paths exist and are accessible before processing
- Handle edge cases: empty files, files with only invalid entries
- Log warnings for recoverable issues, errors for fatal problems
- Ensure output files are written even if some entries fail validation

## Reference Code

```python
import json
import argparse
from collections import Counter

def word_overlap_similarity(text1, text2):
    """Calculate word overlap ratio between two texts"""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    return intersection / union if union > 0 else 0.0

def validate_entry(entry):
    """Validate single JSONL entry"""
    required_fields = ['instruction', 'input', 'output', 'source', 'category']
    
    # Check required fields
    if not all(field in entry for field in required_fields):
        return False, "missing_fields"
    
    # Check non-empty instruction/output
    if not entry['instruction'].strip() or not entry['output'].strip():
        return False, "empty_content"
    
    # Check length limits
    if len(entry['instruction']) >= 500:
        return False, "instruction_too_long"
    if len(entry['output']) >= 5000:
        return False, "output_too_long"
    
    return True, "valid"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input JSONL path')
    parser.add_argument('--output', required=True, help='Output cleaned JSONL path')
    parser.add_argument('--report', required=True, help='Report JSON path')
    args = parser.parse_args()
    
    # Process entries, validate, deduplicate, and generate report
    # Implementation continues...
```