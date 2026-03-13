# JSONL Dataset Validation and Cleaning CLI

## Overview
This skill helps build a robust Python CLI script for validating, cleaning, and deduplicating JSONL training datasets, particularly for materials science or similar domains. It handles real-world data issues like type inconsistencies, memory constraints, and provides detailed reporting.

## Workflow
1. **Setup CLI arguments** with input/output paths and optional features
2. **Load JSONL data** with error handling for malformed JSON
3. **Validate entries** with robust type checking and field requirements
4. **Detect duplicates** using two-stage filtering (shingles + similarity)
5. **Generate comprehensive reports** with statistics and removal reasons
6. **Save cleaned data** and optional duplicate samples for review

## Common Pitfalls
- **Division by zero**: Always check if final dataset is empty before calculating averages
- **Type assumptions**: Real data may have non-string fields, null values, or unexpected types
- **Memory issues**: Long text fields can cause memory problems during similarity calculation
- **Inconsistent duplicate removal**: Ensure first occurrence is always kept, subsequent ones removed
- **Performance bottlenecks**: O(n²) similarity comparison needs optimization for large datasets
- **Overly aggressive filtering**: Simple text signatures miss duplicates with different start/end content

## Error Handling
- Wrap JSON parsing in try-catch for malformed lines
- Add type checking and conversion for all required fields
- Use exception handling in similarity calculations
- Implement memory limits for text processing (max words, max shingles)
- Provide progress indicators for long-running operations

## Quick Reference
