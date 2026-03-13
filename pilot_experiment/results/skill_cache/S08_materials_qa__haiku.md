# SKILL: Materials Science Dataset Validator and Cleaner

## Overview
This tool validates and cleans JSONL datasets for materials science training by checking data integrity, enforcing length constraints, detecting near-duplicates, and generating comprehensive quality reports. It processes line-delimited JSON files and outputs cleaned data with detailed statistics.

## Workflow

### Step 1: Parse Command-Line Arguments
Use `argparse` to accept three required arguments:
- `--input`: Path to source JSONL file
- `--output`: Path for cleaned JSONL output
- `--report`: Path for JSON report output

### Step 2: Load and Parse JSONL
Read the input file line-by-line, parsing each JSON object. Track line numbers for error reporting. Handle malformed JSON gracefully by logging and skipping problematic lines.

### Step 3: Validate Individual Entries
For each entry, verify:
- All required fields exist: `instruction`, `input`, `output`, `source`, `category`
- `instruction` and `output` are non-empty strings
- `instruction` length < 500 characters
- `output` length < 5000 characters
- Mark entries as valid or invalid with reason codes

### Step 4: Detect Near-Duplicates
Build a similarity matrix using word overlap ratio (Jaccard similarity) on instruction fields. Flag pairs with similarity > 0.9. Keep first occurrence, mark subsequent duplicates for removal.

### Step 5: Filter and Write Cleaned Data
Remove all invalid and duplicate entries. Write remaining entries to output JSONL file, preserving original structure.

### Step 6: Generate Statistics Report
Compile metrics:
- Total entries processed
- Removal counts by reason (missing fields, length violation, duplicate)
- Category distribution (count per category)
- Average instruction and output lengths
- Write report as formatted JSON

### Step 7: Output Summary
Log processing results to console and save report file.

## Common Pitfalls & Solutions

| Pitfall | Problem | Solution |
|---------|---------|----------|
| **Memory overflow on large files** | Loading entire JSONL into memory fails on datasets > 1GB | Process line-by-line; store only instruction text for duplicate detection, not full entries |
| **Incorrect similarity threshold** | Word overlap ratio > 0.9 too strict/loose | Validate threshold on sample data; consider using difflib.SequenceMatcher for alternative metrics |
| **Encoding issues** | Non-UTF8 characters cause JSON parsing errors | Open files with `encoding='utf-8'` and use `errors='replace'` parameter |
| **Duplicate detection inefficiency** | O(n²) comparison on large datasets is slow | Use MinHash or locality-sensitive hashing for approximate matching on 10k+ entries |
| **Silent data loss** | Invalid entries removed without clear tracking | Log every removal with line number, reason, and entry preview to separate error log |

## Error Handling Tips

- **Wrap JSON parsing** in try-except blocks; log line number and raw content for debugging
- **Validate field types** explicitly (strings for instruction/output, not null/int)
- **Handle edge cases**: empty strings after whitespace stripping, Unicode normalization
- **Create fallback categories**: assign "unknown" category if missing rather than rejecting
- **Report non-fatal warnings**: log length warnings separately from hard failures
- **Atomic writes**: write to temporary file, then rename to avoid corrupted output on crash

## Reference Code Snippet

```python
import json
import argparse
from collections import defaultdict, Counter
from difflib import SequenceMatcher

def word_overlap_ratio(text1, text2):
    """Calculate Jaccard similarity of word sets."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    if not words1 or not words2:
        return 0.0
    intersection = len(words1 & words2)
    union = len(words1 | words2)
    return intersection / union if union > 0 else 0.0

def validate_entry(entry, line_num):
    """Validate single entry. Return (is_valid, reason)."""
    required = {'instruction', 'input', 'output', 'source', 'category'}
    if not all(k in entry for k in required):
        return False, "missing_fields"
    if not isinstance(entry['instruction'], str) or not entry['instruction'].strip():
        return False, "empty_instruction"
    if not isinstance(entry['output'], str) or not entry['output'].strip():
        return False, "empty_output"
    if len(entry['instruction']) >= 500:
        return False, "instruction_too_long"
    if len(entry['output']) >= 5000:
        return False, "output_too_long"
    return True, "valid"

def process_dataset(input_path, output_path, report_path):
    entries = []
    removal_reasons = Counter()
    categories = Counter()
    lengths = {'instruction': [], 'output': []}
    
    # Load and validate
    with open(input_path, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                is_valid, reason = validate_entry(entry, line_num)
                if is_valid:
                    entries.append(entry)
                    categories[entry['category']] += 1
                    lengths['instruction'].append(len(entry['instruction']))
                    lengths['output'].append(len(entry['output']))
                else:
                    removal_reasons[reason] += 1
            except json.JSONDecodeError:
                removal_reasons['malformed_json'] += 1
    
    # Detect duplicates
    duplicates = set()
    for i, e1 in enumerate(entries):
        for j, e2 in enumerate(entries[i+1:], i+1):
            if word_overlap_ratio(e1['instruction'], e2['instruction']) > 0.9:
                duplicates.add(j)
                removal_reasons['duplicate'] += 1
    
    # Write cleaned data
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, entry in enumerate(entries):
            if i not in duplicates:
                f.write(json.dumps(entry) + '\n')
    
    # Generate report
    report = {
        'total_entries': line_num,
        'removed_count': sum(removal_reasons.values()),
        'removal_reasons': dict(removal_reasons),
        'category_distribution': dict(categories),
        'avg_instruction_length': sum(lengths['instruction']) / len(lengths['instruction']) if lengths['instruction'] else 0,
        'avg_output_length': sum(lengths['output']) / len(lengths['output']) if lengths['output'] else 0
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--report', required=True)
    args = parser.parse_args()
    process_dataset(args.input, args.output, args.report)
```