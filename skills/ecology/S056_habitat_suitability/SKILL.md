---
name: habitat_suitability
description: "# Habitat Suitability Index Calculator

Create a CLI script that calculates habitat suitability indices for species based on multiple environmental variables. The script should process synthetic environmental data and generate comprehensive analysis outputs including visualizations and statistics."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: ecology
---

# Habitat Suitability Index Calculator

## Overview
A comprehensive tool for calculating Habitat Suitability Index (HSI) values based on environmental variables. The system generates synthetic environmental data layers (temperature, precipitation, elevation, vegetation) and computes weighted suitability scores to identify optimal habitat locations for target species.

## When to Use
- Ecological research requiring habitat suitability modeling
- Conservation planning and species distribution analysis
- Environmental impact assessments
- Wildlife management decision support
- Academic research in landscape ecology

## Inputs
- Species name (string with spaces allowed)
- Environmental parameter weights (4 comma-separated values summing to 1.0)
- Temperature range preferences (min,max format)
- Minimum precipitation threshold
- Grid size for analysis resolution
- Output directory path

## Workflow
1. Execute scripts/main.py with required CLI arguments
2. System generates synthetic environmental data layers with spatial correlation
3. Individual suitability scores calculated for each environmental factor
4. Weighted HSI computed using user-specified factor weights
5. Summary statistics calculated including optimal locations
6. Outputs saved as CSV, JSON, and PNG visualization files
7. Reference references/pitfalls.md for common error handling patterns

## Error Handling
The system includes robust error handling for memory management and file operations. Large datasets are processed in chunks to handle memory constraints efficiently. Weight validation ensures proper mathematical constraints are met. Filename sanitization prevents filesystem errors when species names contain special characters.

## Common Pitfalls
- Memory issues with large grid sizes require chunked processing
- Species names with spaces need filename sanitization
- Weight validation must sum to exactly 1.0
- Spatial correlation parameters affect data realism

## Output Format
- CSV file: HSI grid values as tabular data
- JSON file: Summary statistics with mean HSI, suitable habitat percentage, top 5 optimal locations
- PNG file: Heatmap visualization with color-coded suitability values
- Console logs: Processing status and key metrics
