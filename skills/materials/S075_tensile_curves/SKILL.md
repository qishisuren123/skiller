---
name: tensile_curves
description: "# Tensile Test Curve Analysis

Create a CLI script that processes tensile test stress-strain data and extracts key mechanical properties from the curves.

Your script should accept tensile test data c"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: materials
---

# Tensile Curves

## Overview
A comprehensive CLI tool for analyzing tensile test stress-strain curves and extracting key mechanical properties. The script generates realistic tensile curves with both elastic and plastic regions, calculates elastic modulus, yield strength (0.2% offset method), and ultimate tensile strength, then outputs both visualizations and structured results.

## When to Use
- Materials engineering analysis of stress-strain behavior
- Educational demonstrations of tensile testing concepts
- Batch processing of tensile test parameter studies
- Quality control validation of material properties
- Research requiring realistic tensile curve generation

## Inputs
- `--points`: Number of data points (default: 1000, minimum 20 recommended)
- `--max_stress`: Maximum stress in MPa (default: 500)
- `--max_strain`: Maximum strain (default: 0.25)
- `--plot_file`: Output plot filename (default: tensile_curve.png)
- `--results_file`: Output JSON filename (default: results.json)
- `--verbose`: Enable detailed logging

## Workflow
1. Execute `scripts/main.py` with desired parameters
2. Script validates input parameters and warns of potential reliability issues
3. Generates realistic stress-strain curve with adaptive yield behavior
4. Calculates elastic modulus using linear regression on elastic region
5. Determines yield strength using 0.2% offset method
6. Creates visualization with marked key points and offset line
7. Outputs JSON results and saves plot
8. Consult `references/pitfalls.md` for common error scenarios and fixes

## Error Handling
The script includes comprehensive error handling for edge cases. It validates parameters to handle unrealistic inputs, checks for insufficient data points that could cause calculation failures, and converts numpy NaN/inf values to JSON-compatible format. Logging tracks each calculation step to help users understand when results may be unreliable due to parameter choices.

## Common Pitfalls
- Using too few data points (<50) leads to unreliable calculations
- Very small strain ranges may not capture full material behavior
- JSON serialization fails with numpy NaN values without proper conversion
- Hardcoded offset line ranges can extend beyond actual data bounds
- Array dimension mismatches occur with extreme parameter combinations

## Output Format
- PNG plot showing stress-strain curve with marked properties
- JSON file containing elastic_modulus, yield_strength, ultimate_tensile_strength, strain_at_failure
- Log file with detailed analysis steps and warnings
- Console output summarizing key calculated properties
