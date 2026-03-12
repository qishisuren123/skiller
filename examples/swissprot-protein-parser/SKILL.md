---
name: swissprot-protein-parser
description: "解析SwissProt数据库的JSON格式蛋白质描述数据。SwissProt包含大量自然语言描述的蛋白质功能信息，格式复杂、信息杂乱。需要提取蛋白质ID、名称、功能描述、GO注释、亚细胞定位、序列信息等结构化字段，输出为标准化的CSV/JSON格式。工具: mmseqs/foldseek可用于后续序列搜索。 Use this skill when the user needs to 解析swissprot数据库的json格式蛋白质描述数据。swissprot包含大量自然语言描述的蛋白质功能信息，格式复杂、信息杂乱。需要提取蛋白质id、名称、功能描述、go注释、亚细胞定位、序列信息."
license: MIT
compatibility: "Python >=3.9; json, pandas, numpy, re"
metadata:
  author: conversation-to-skill-generator
  version: "1.0"
---

# Swissprot Protein Parser

## Overview
Parses SwissProt protein database JSON files into structured CSV or JSON format. Handles complex nested JSON structures with natural language protein descriptions, extracting key fields like protein ID, name, function, GO annotations, subcellular localization, and sequence data. Optimized for large datasets (500K+ entries) with streaming processing to handle memory constraints.

## When to Use
- Processing SwissProt protein database exports in JSON format
- Converting unstructured protein data to structured formats for analysis
- Extracting specific protein attributes from complex nested JSON
- Preparing protein data for downstream bioinformatics tools (mmseqs, foldseek)
- Handling large-scale protein datasets that exceed memory limits

## Inputs
- **input_file**: SwissProt JSON file (list of entries or nested structure)
- **output_file**: Target CSV or JSON output file
- **format**: Output format ('csv' or 'json')
- **batch_size**: Processing batch size (default: 1000)
- **stats_file**: Optional statistics output file

## Workflow
1. Load and validate input JSON structure using `scripts/main.py`
2. Process entries in batches to manage memory usage
3. Extract structured fields using safe parsing functions
4. Handle edge cases like empty arrays and malformed entries
5. Stream write results to avoid memory overflow
6. Generate parsing statistics and error reports
7. Reference `references/pitfalls.md` for common error patterns

## Error Handling
The parser includes comprehensive error handling for malformed JSON entries. Each entry is processed individually with try-catch blocks to handle parsing errors gracefully. Memory errors are prevented through streaming batch processing. Failed entries are logged with specific error messages for debugging.

## Common Pitfalls
- Assuming consistent JSON structure across all entries
- Loading entire dataset into memory causing MemoryError
- Not handling empty text arrays in comment sections
- Ignoring data type inconsistencies leading to pandas warnings
- Missing UTF-8 encoding causing character corruption

## Quick Reference

```bash
# Parse SwissProt JSON to CSV
python scripts/main.py input_swissprot.json -o output.csv -f csv --batch-size 1000

# Parse to JSON with statistics
python scripts/main.py input_swissprot.json -o output.json -f json --stats stats.json
```

```python
# Core parsing pattern for SwissProt entries
def parse_entry(entry):
    return {
        'protein_id': entry.get('primaryAccession', ''),
        'protein_name': entry.get('proteinDescription', {})
            .get('recommendedName', {}).get('fullName', {}).get('value', ''),
        'function': ' '.join(
            t.get('value', '') for c in entry.get('comments', [])
            if c.get('commentType') == 'FUNCTION'
            for t in c.get('texts', [])
        ),
        'go_annotations': ';'.join(
            ref.get('id', '') for ref in entry.get('uniProtKBCrossReferences', [])
            if ref.get('database') == 'GO'
        ),
    }
```

## Output Format
**CSV**: Structured table with columns: protein_id, protein_name, function_description, go_annotations, subcellular_location, sequence, sequence_length

**JSON**: Nested structure with metadata and entries array, including parsing statistics and total counts
