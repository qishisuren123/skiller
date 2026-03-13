# Materials Science QA Dataset Cleaning — Expert Notes

## What You're Building
Validate and clean a JSONL training dataset: check required fields, remove invalid entries, detect near-duplicates, generate a quality report.

## Key Steps
1. Read JSONL line by line with `json.loads`
2. Validate each entry: required fields present, non-empty instruction/output, length limits
3. Detect near-duplicates by word overlap ratio
4. Write cleaned JSONL + report JSON

## Pitfalls I've Hit
1. **JSONL != JSON**: Read line by line, not `json.load(file)`. Each line is one JSON object
2. **Empty lines**: Skip blank lines. Some JSONL files have trailing newlines
3. **Field validation order**: Check field existence BEFORE checking values. `entry.get("instruction", "")` is safer than `entry["instruction"]`
4. **Duplicate detection**: Simple word overlap works fine. `set(a.split()) & set(b.split())` / `set(a.split()) | set(b.split())`. Don't overthink it — Jaccard similarity > 0.9 catches obvious dupes
5. **Length limits**: Check `len(instruction) < 500` and `len(output) < 5000` AFTER stripping whitespace

## Reference
```python
def word_overlap(a, b):
    wa, wb = set(a.lower().split()), set(b.lower().split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)

cleaned = []
removed = {"empty": 0, "missing_field": 0, "too_long": 0, "duplicate": 0}
seen_instructions = []
for entry in entries:
    if not all(f in entry for f in required_fields):
        removed["missing_field"] += 1
        continue
    if not entry["instruction"].strip():
        removed["empty"] += 1
        continue
    if any(word_overlap(entry["instruction"], s) > 0.9 for s in seen_instructions):
        removed["duplicate"] += 1
        continue
    seen_instructions.append(entry["instruction"])
    cleaned.append(entry)
```
