---
name: disulfide_bonds
description: "# Disulfide Bond Detection and Validation

Create a CLI script that analyzes protein structures to detect and validate disulfide bonds between cysteine residues based on atomic distances and geometric"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: biology
---

# Disulfide Bonds

## Overview
A comprehensive CLI tool for analyzing protein structures to detect and validate disulfide bonds between cysteine residues. The tool performs distance-based detection, geometric validation using C-S-S bond angles, and provides detailed analysis output with validation statistics.

## When to Use
- Analyzing protein structures from PDB data in JSON format
- Validating potential disulfide bonds in protein models
- Quality control for protein structure predictions
- Research requiring geometric validation of cysteine cross-links
- Batch processing of multiple protein structures

## Inputs
- **PDB JSON file**: Protein structure data with chains, residues, and atomic coordinates
- **Distance cutoff**: Maximum S-S distance threshold (default: 2.5 Å)
- **Angle tolerance**: Deviation tolerance for C-S-S angles (default: 20°)
- **Energy model**: Calculation approach (simple/advanced)

## Workflow
1. Execute `scripts/main.py` with input PDB JSON file
2. Tool extracts cysteine residues and locates SG/CB atoms
3. Distance-based filtering identifies potential S-S bonds
4. Geometric validation calculates C-S-S bond angles (~104°)
5. Results saved with validation statistics and bond details
6. Consult `references/pitfalls.md` for common error handling patterns

## Error Handling
The tool includes robust error handling for JSON serialization issues, numpy array conversion problems, and geometric calculation edge cases. When zero-length vectors cause division errors in angle calculations, the system logs warnings and handles NaN values gracefully to prevent crashes.

## Common Pitfalls
- JSON serialization fails with numpy arrays - convert to lists before saving
- Missing coordinates in carbon_coords array creation
- Division by zero in angle calculations with identical atom positions
- Improper handling of edge cases in geometric validation

## Output Format
JSON structure containing analysis parameters, summary statistics (total cysteines, validated bonds, inter/intra-chain counts), and detailed bond information with geometric validation results including C-S-S angles and deviations.
