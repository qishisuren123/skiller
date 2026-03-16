---
name: materials_qa_dataset_cleaner
description: "Python CLI script to validate and clean materials science training datasets stored as JSONL format. Handles duplicate detection using LSH optimization, validates required fields, and generates comprehensive cleaning reports."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: materials
---

# Materials QA Dataset Cleaner

## Overview
A Python CLI tool for cleaning and validating materials science training datasets in JSONL format. Uses Locality-Sensitive Hashing (LSH) with MinHash signatures for efficient duplicate detection on large datasets (15,000+ entries). Validates required fields, removes near-duplicates based on instruction similarity, and generates detailed cleaning reports.

## When to Use
- Cleaning materials science Q&A datasets before training
- Removing duplicate questions with similar phrasing
- Validating dataset structure and field completeness
- Generating statistics on dataset composition
- Processing large JSONL datasets efficiently (handles 15K+ entries in minutes)

## Inputs
- Input JSONL file with fields: instruction, input, output, source, category
- Similarity threshold for duplicate detection (default: 0.85)
- Output paths for cleaned data and report
- Optional debug mode for detailed logging

## Workflow
1. Load and parse JSONL entries using scripts/main.py
2. Validate each entry for required fields and content quality
3. Generate MinHash signatures for efficient similarity comparison
4. Use LSH bucketing to find candidate duplicate pairs
5. Apply precise n-gram similarity scoring to candidates
6. Remove duplicates while preserving first occurrence
7. Generate comprehensive statistics and cleaning report
8. Output cleaned JSONL and JSON report files
9. Reference references/pitfalls.md for common error patterns

## Error Handling
The tool includes robust error handling for JSON parsing failures, missing fields, and empty content. When the system encounters malformed JSON lines, it logs warnings and continues processing. Division by zero errors are handled by checking for empty result sets before calculating averages. File I/O errors are caught and reported with clear error messages to help users diagnose issues.

## Common Pitfalls
- Using simple word overlap for similarity leads to false positives with domain-specific terms
- O(n²) comparison algorithms become prohibitively slow on large datasets
- Counter objects require explicit conversion to dict for JSON serialization
- Heavy dependencies like scikit-learn may not be available in all environments

## Output Format
Produces cleaned JSONL file with validated entries and JSON report containing:
- Total and cleaned entry counts
- Removal reasons breakdown
- Category distribution statistics  
- Average instruction and output lengths
- Similarity threshold used
