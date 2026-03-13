# SKILL: JSONL Materials Science Dataset Validator and Cleaner

## Overview
A Python CLI tool that validates, cleans, and deduplicates materials science training datasets in JSONL format. The tool ensures data quality by checking field requirements, enforcing length limits, removing near-duplicates based on instruction similarity, and generating detailed cleaning reports.

## Step-by-Step Workflow

1. **Parse Command Line Arguments**
   - Accept `--input` for source JSONL file path
   - Accept `--output` for cleaned JSONL file path
   - Accept `--report` for JSON report output path

2. **Load and Parse JSONL Data**
   - Read file line by line to handle large datasets
   - Parse each line as JSON, tracking line numbers for error reporting

3. **Validate Each Entry**
   - Check presence of required fields: `instruction`, `input`, `output`, `source`, `category`
   - Verify `instruction` and `output` are non-empty strings
   - Enforce length limits: instruction < 500 chars, output < 5000 chars

4. **Detect Near-Duplicates**
   - Calculate word overlap ratio between instructions
   - Flag entries with similarity > 0.9 as duplicates
   - Keep only the first occurrence of duplicate groups

5. **Filter and Clean Data**
   - Remove entries failing validation
   - Remove duplicate entries (keeping first occurrence)
   - Track removal reasons for reporting

6. **Write Cleaned Dataset**
   - Output valid, unique entries to new JSONL file
   - Maintain original JSON structure for each entry

7. **Generate Analysis Report**
   - Calculate statistics: total entries, removal counts by reason
   - Compute category distribution and average field lengths
   - Save report as formatted JSON

## Common Pitfalls and Solutions

### 1. **Memory Issues with Large Files**
- **Problem**: Loading entire file into memory causes crashes
- **Solution**: Process line by line using file iterator, store only necessary data for duplicate detection

### 2. **Unicode/Encoding Errors**
- **Problem**: Special characters in scientific text cause parsing failures
- **Solution**: Open files with `encoding='utf-8'` and handle encoding errors gracefully

### 3. **Incomplete JSON Lines**
- **Problem**: Corrupted or truncated lines break JSON parsing
- **Solution**: Wrap JSON parsing in try-except, log problematic line numbers, continue processing

### 4. **Case Sensitivity in Duplicate Detection**
- **Problem**: "HEAT treatment" and "heat treatment" not detected as similar
- **Solution**: Convert to lowercase before calculating similarity, preserve original case in output

### 5. **Empty or Whitespace-Only Fields**
- **Problem**: Fields containing only spaces pass empty checks
- **Solution**: Use `str.strip()` before checking if fields are empty

## Error Handling Tips

- **Graceful Degradation**: Continue processing even if individual entries fail
- **Detailed Logging**: Track line numbers and specific validation failures
- **Atomic Operations**: Write to temporary file first, then rename to avoid data loss
- **Validation Counts**: Maintain counters for each type of validation failure
- **Early Exit Options**: Add `--strict` flag to stop on first error if needed

## Reference Code Snippet

```python
def calculate_word_overlap_ratio(text1, text2):
    """Calculate word overlap ratio for duplicate detection."""
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1 & words2
    union = words1 | words2
    
    return len(intersection) / len(union)

def validate_entry(entry, line_num):
    """Validate a single JSONL entry."""
    errors = []
    
    # Check required fields
    required_fields = ['instruction', 'input', 'output', 'source', 'category']
    for field in required_fields:
        if field not in entry:
            errors.append(f"Missing field: {field}")
    
    if errors:
        return False, errors
    
    # Check non-empty and length constraints
    if not entry['instruction'].strip():
        errors.append("Empty instruction")
    elif len(entry['instruction']) > 500:
        errors.append(f"Instruction too long: {len(entry['instruction'])} chars")
    
    if not entry['output'].strip():
        errors.append("Empty output")
    elif len(entry['output']) > 5000:
        errors.append(f"Output too long: {len(entry['output'])} chars")
    
    return len(errors) == 0, errors
```