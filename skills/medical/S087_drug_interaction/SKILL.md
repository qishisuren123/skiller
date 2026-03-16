---
name: drug_interaction_analysis
description: "# Drug Interaction Analysis Tool

Create a CLI script that analyzes prescription data to identify potential drug interactions and generate safety reports with customizable risk scoring and filtering options."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: medical
---

# Drug Interaction Analysis

## Overview
A comprehensive CLI tool for analyzing prescription data to identify potential drug interactions, calculate patient risk scores, and generate detailed safety reports. The tool handles brand-to-generic drug name mapping, provides customizable severity scoring, and supports filtering for high-risk patients.

## When to Use
- Pharmacy research and safety analysis
- Clinical decision support systems
- Drug interaction surveillance programs
- Patient safety audits
- Regulatory compliance reporting

## Inputs
- CSV file with prescription data (columns: patient_id, drug_name, dosage, prescription_date)
- Optional drug mapping file for brand-to-generic conversions
- Configurable parameters for risk scoring and filtering

## Workflow
1. Load prescription data using `scripts/main.py` with date format handling
2. Apply drug name normalization using brand-to-generic mapping
3. Find concurrent medications within specified time window
4. Check interactions against built-in database
5. Calculate patient risk scores with customizable severity weights
6. Generate comprehensive reports (JSON, CSV, visualization)
7. Filter high-risk patients based on threshold
8. Reference `references/workflow.md` for detailed steps

## Error Handling
The system includes robust error handling for common issues:
- Date parsing errors with multiple format attempts
- Empty datasets that would cause visualization failures
- Missing drug mappings with fallback to original names
- Performance optimization for large datasets
- CSV serialization issues with timestamp objects

## Common Pitfalls
- Date format mismatches between data and parser expectations
- Duplicate interaction records from improper deduplication
- Performance bottlenecks with nested loops on large datasets
- Brand vs generic name mismatches in interaction database
- Timestamp serialization errors in output generation

## Output Format
- JSON report with detailed interaction analysis
- CSV file with all detected interactions
- Risk score histogram visualization
- High-risk patient summary (when threshold specified)
- Comprehensive logging of analysis statistics
