---
name: species_accumulation
description: "# Species Accumulation Curve Analysis

Create a CLI script that computes and analyzes species accumulation curves from ecological sampling data. Species accumulation curves show how the cumulative number of species increases with sampling effort, essential for biodiversity assessment and sampling completeness evaluation."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: ecology
---

# Species Accumulation Curve Analysis

## Overview
This skill creates a comprehensive CLI tool for species accumulation curve analysis in ecological research. The tool generates synthetic ecological data, computes species accumulation curves with confidence intervals, performs sample-based rarefaction analysis, and calculates asymptotic richness estimates using the Chao2 estimator. It provides both statistical analysis and visualization capabilities for biodiversity assessment.

## When to Use
- Analyzing biodiversity patterns across sampling sites
- Evaluating sampling completeness in ecological surveys
- Comparing species richness between different habitats or regions
- Planning future sampling efforts based on accumulation curves
- Teaching ecological statistics and biodiversity concepts
- Generating synthetic data for method testing and validation

## Inputs
- Number of sampling sites (default: 50)
- Species pool size for synthetic data (default: 100)
- Number of randomizations for confidence intervals (default: 100)
- Output directory path (default: 'output')
- Random seed for reproducibility (default: 42)

## Workflow
1. Execute `scripts/main.py` with desired parameters
2. Script generates synthetic occurrence data with realistic species rarity patterns
3. Computes species accumulation curves using random site orderings
4. Performs sample-based rarefaction analysis with numerical stability
5. Calculates Chao2 asymptotic richness estimator
6. Creates comprehensive visualization with confidence bands
7. Exports results to JSON and CSV formats
8. Refer to `references/workflow.md` for detailed step-by-step process
9. Check `references/pitfalls.md` for common error handling scenarios

## Error Handling
The tool includes robust error handling for numerical overflow issues in rarefaction calculations. When binomial coefficients become too large, the system automatically switches to scipy's floating-point implementation and includes fallback approximations. The error handling ensures stable computation even with large datasets (200+ sites, 500+ species) by using exact=False parameters and hypergeometric approximations when needed.

## Common Pitfalls
- Integer overflow in binomial coefficient calculations with large datasets
- Memory issues with excessive randomizations on large site counts
- Incorrect species frequency calculations leading to invalid Chao2 estimates
- Visualization scaling problems with extreme richness values
- File path conflicts when output directory doesn't exist

## Output Format
- `occurrence_matrix.csv`: Site-by-species occurrence matrix
- `species_accumulation_plot.png`: Comprehensive visualization with curves and statistics
- `analysis_results.json`: Complete numerical results including confidence intervals
- Console output with key summary statistics and file locations
