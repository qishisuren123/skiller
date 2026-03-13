Write a Python CLI script to validate and clean a materials science training dataset stored as JSONL (one JSON per line).

Each line has fields: instruction, input, output, source, category.

Requirements:
1. Use argparse: --input JSONL path, --output cleaned JSONL path, --report JSON path
2. Validate each entry: check all required fields present, instruction/output not empty, length limits (instruction < 500 chars, output < 5000 chars)
3. Detect near-duplicates: flag entries where instruction similarity (by word overlap ratio) > 0.9
4. Remove invalid entries and duplicates, write cleaned data
5. Generate report JSON: total entries, removed count (by reason), category distribution, average lengths
