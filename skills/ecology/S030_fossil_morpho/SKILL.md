---
name: fossil_morpho
description: "Write a Python CLI script to perform morphometric analysis on fossil specimen measurements.

Input: A CSV file with columns:
- specimen_id, taxon, length_mm, width_mm, height_mm, mass_g, formation, epoch"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: ecology
---

# Fossil Morpho

## Overview
A comprehensive Python CLI tool for morphometric analysis of fossil specimens. Computes shape indices (elongation, flatness, sphericity), performs PCA on standardized measurements, and generates grouped statistics by taxon and epoch. Includes robust data validation to handle missing values and measurement errors.

## When to Use
- Analyzing fossil specimen measurements for morphological patterns
- Computing standardized shape indices for comparative studies
- Performing dimensionality reduction on morphometric data
- Generating taxonomic and temporal group statistics
- Processing large datasets (optimized for 15,000+ specimens)

## Inputs
- CSV file with columns: specimen_id, taxon, length_mm, width_mm, height_mm, mass_g, formation, epoch
- Output directory path for results

## Workflow
1. Execute `scripts/main.py` with input CSV and output directory
2. Script validates measurements and handles non-positive values
3. Computes shape indices with division-by-zero protection
4. Performs memory-efficient PCA using sklearn
5. Generates grouped statistics by taxon and epoch
6. Outputs three files: morphometrics.csv, pca_results.csv, taxon_summary.json
7. Refer to `references/workflow.md` for detailed steps

## Error Handling
The script includes comprehensive error handling for common data issues. Missing values are properly handled during PCA computation, and non-positive measurements are converted to NaN to prevent infinite values in shape calculations. Memory optimization prevents crashes on large datasets through efficient matrix operations.

## Common Pitfalls
- Division by zero in shape indices (fixed with conditional calculations)
- PCA convergence failures from missing data (resolved with proper preprocessing)
- Memory issues on large datasets (optimized with sklearn and chunked processing)
- Dimension mismatches in PCA output (corrected DataFrame construction)

## Output Format
- morphometrics.csv: All specimens with computed shape indices and PC scores
- pca_results.csv: Component loadings and explained variance ratios
- taxon_summary.json: Grouped statistics by taxon and epoch
- Console summary with key analysis metrics
