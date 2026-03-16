---
name: rmsd_alignment
description: "# Protein Structure RMSD Alignment Tool

Create a command-line tool that performs structural alignment of protein conformations and computes Root Mean Square Deviation (RMSD) values using the Kabsch algorithm with SVD optimization."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: biology
---

# RMSD Alignment

## Overview

This skill creates a robust protein structure alignment tool that computes RMSD values and performs optimal structural alignment using the Kabsch algorithm. The tool handles molecular dynamics simulation data with varying atom counts and provides memory-optimized processing for large protein structures.

## When to Use

- Aligning protein conformations from MD simulations
- Computing structural similarity between protein states
- Optimizing molecular overlays for comparative analysis
- Processing large biomolecular datasets with memory constraints
- Batch alignment of multiple protein structures

## Inputs

- Reference structure coordinates file (xyz format)
- Target structure coordinates file (xyz format)
- Optional: maximum atom count for subsampling
- Optional: atom matching method (truncate/pad)
- Optional: subsampling method (uniform/random)

## Workflow

1. Execute scripts/main.py with coordinate files as arguments
2. Load and validate coordinate data from input files
3. Handle atom count mismatches using truncation or padding
4. Apply memory-efficient subsampling for large structures
5. Center coordinates at centroids for both structures
6. Perform Kabsch alignment using SVD decomposition
7. Compute rotation matrix and apply optimal transformation
8. Calculate initial and final RMSD values
9. Save aligned coordinates and generate JSON report
10. Reference references/workflow.md for detailed step-by-step process

## Error Handling

The tool includes comprehensive error handling for common issues:
- Memory errors during large structure processing are handled through chunked operations
- Atom count mismatches are automatically resolved using specified matching methods
- Invalid coordinate formats trigger informative error messages
- SVD computation failures are caught and reported with diagnostic information
- File I/O errors provide clear guidance for resolution

## Common Pitfalls

- Memory allocation failures with very large structures (>50K atoms)
- Numpy version compatibility issues with matrix transpose operations
- Atom count mismatches between reference and target structures
- Coordinate file format inconsistencies
- Insufficient available memory for covariance matrix computation

## Output Format

- Aligned coordinate file in xyz format
- JSON report containing alignment statistics and transformation parameters
- Console output with RMSD values and improvement percentage
- Rotation matrix and centroid information
- Memory usage and performance metrics
