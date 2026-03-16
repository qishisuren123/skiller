---
name: bfactor_analysis
description: "# B-Factor Analysis Tool

Create a command-line tool that analyzes B-factor (temperature factor) distributions in protein structures and identifies flexible regions. B-factors indicate atomic displacement and structural flexibility in proteins."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: biology
---

# B-Factor Analysis

## Overview
This tool analyzes B-factor (temperature factor) distributions in protein structures to identify flexible regions. B-factors represent atomic displacement parameters that indicate structural flexibility - higher values suggest more mobile/flexible regions. The tool calculates statistical measures, identifies flexible regions above a threshold, groups consecutive flexible residues into segments, and creates visualizations.

## When to Use
- Analyzing protein flexibility from crystallographic B-factor data
- Identifying mobile loops and flexible regions in protein structures
- Comparing flexibility patterns between different protein conformations
- Quality assessment of structural data based on B-factor distributions
- Preparing flexibility analysis for molecular dynamics simulations

## Inputs
- **B-factor values**: Comma-separated list of B-factor values for each residue
- **Output file**: JSON file path for analysis results (optional)
- **Normalization**: Flag to normalize B-factors to 0-100 scale (optional)
- **Plot prefix**: Filename prefix for visualization output (optional)

## Workflow
1. Execute `scripts/main.py` with B-factor data as command-line argument
2. Parse and validate input B-factor values from comma-separated string
3. Calculate comprehensive statistics (mean, median, std, quartiles, min/max)
4. Identify flexible regions using 75th percentile threshold
5. Group consecutive flexible residues into contiguous segments
6. Generate line plot visualization with highlighted flexible regions
7. Save analysis results to JSON file and plot to PNG file
8. Reference `references/workflow.md` for detailed step-by-step process

## Error Handling
The tool includes robust error handling for common issues. JSON serialization errors are handled by converting NumPy data types to native Python types before saving. Index out of range errors in plotting are handled by proper coordinate system conversion between 1-based residue numbering and 0-based array indexing. Input validation ensures B-factor values are properly parsed from command-line strings.

## Common Pitfalls
- **JSON Serialization**: NumPy float64 objects are not JSON serializable - always convert to Python float() before saving
- **Index Conversion**: Flexible residues use 1-based numbering but array indexing requires 0-based conversion
- **Missing Dependencies**: Ensure matplotlib and numpy are installed for plotting functionality
- **Empty Segments**: Handle edge cases where no residues exceed the flexibility threshold

## Output Format
- **JSON Results**: Statistical summary, flexible residue list, segment groupings, and threshold value
- **PNG Visualization**: Line plot showing B-factor distribution with highlighted flexible regions and threshold line
- **Console Output**: Summary statistics, flexible region count, and file locations
