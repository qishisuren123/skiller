---
name: dicom_metadata
description: "# DICOM Metadata Extraction and Validation Tool

Create a CLI tool that processes synthetic DICOM-like medical imaging metadata to extract, validate, and analyze patient and study information across multiple series with memory-efficient streaming processing."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: medical
---

# DICOM Metadata Extraction and Validation Tool

## Overview
A comprehensive CLI tool for processing DICOM-like medical imaging metadata stored in JSON format. The tool provides validation, anonymization, and statistical analysis capabilities while handling large datasets efficiently through streaming processing and memory optimization techniques.

## When to Use
- Processing synthetic DICOM metadata for compliance validation
- Anonymizing patient data while preserving medical information
- Generating statistical reports on imaging study parameters
- Validating nested series data within studies
- Handling large datasets (10,000+ studies) with memory constraints
- Creating compliance reports for medical imaging workflows

## Inputs
- **input-data**: JSON file containing DICOM metadata with nested series structure
- **validation-rules** (optional): JSON file with custom validation rules
- **anonymize** flag: Enable patient data anonymization
- **batch-size**: Configure memory usage for large datasets

## Workflow
1. Load validation rules from references/validation_rules.json if provided
2. Stream records in configurable batches using scripts/main.py processing pipeline
3. Apply anonymization with consistent patient ID hashing and date shifting
4. Validate each study and nested series against DICOM standards
5. Generate incremental statistics to avoid memory overflow
6. Output validation report and statistical summary
7. Handle error conditions and log processing progress

## Error Handling
The tool implements comprehensive error handling for common issues:
- **File Loading Errors**: Gracefully handle missing or corrupted input files with informative error messages
- **Memory Management**: Use streaming processing and garbage collection to handle large datasets without memory overflow
- **Date Format Validation**: Detect and report invalid date formats while continuing processing
- **Nested Structure Issues**: Properly handle missing or malformed series data within studies
- **Dictionary Modification Errors**: Use selective copying instead of in-place modification to avoid runtime errors during iteration

## Common Pitfalls
- **Memory Exhaustion**: Large datasets can overwhelm memory if not processed in batches
- **Nested Data Access**: Series-level data must be accessed through the Series array, not directly on study records
- **In-Place Modification**: Modifying dictionaries during iteration causes runtime errors
- **Date Consistency**: Patient anonymization requires consistent date shifting across all studies
- **Deep Copy Performance**: Full deep copying is memory-intensive; use selective copying instead

## Output Format
- **Validation Report**: JSON file with summary statistics and detailed violation records
- **Statistical Summary**: JSON file with parameter distributions and institutional statistics
- **Progress Logging**: Real-time processing status with batch completion indicators
- **Error Reports**: Structured logging of validation failures and data quality issues
