---
name: spirometry_flow
description: "# Spirometry Flow-Volume Analysis

Create a CLI script that processes spirometry flow-volume data and computes key pulmonary function parameters.

Spirometry is a common pulmonary function test that m"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: medical
---

# Spirometry Flow-Volume Analysis

## Overview
This skill creates a CLI tool for analyzing spirometry flow-volume data and computing key pulmonary function parameters including FEV1, FVC, and their ratio. The tool generates synthetic spirometry data with realistic flow patterns, performs clinical parameter calculations, validates results against physiological ranges, and outputs both visualizations and structured results.

## When to Use
- Pulmonary function research requiring synthetic spirometry data
- Clinical validation of spirometry analysis algorithms
- Educational demonstrations of flow-volume loop analysis
- Performance testing of respiratory analysis pipelines
- Batch processing of spirometry parameter calculations

## Inputs
- `--n-points`: Number of data points to generate (default: 1000)
- `--plot-file`: Output plot filename (default: flow_volume_loop.png)
- `--results-file`: Output JSON results filename (default: spirometry_results.json)

## Workflow
1. Execute `scripts/main.py` with desired parameters
2. Script generates synthetic spirometry data with realistic flow patterns
3. Calculates FEV1 (forced expiratory volume in 1 second) using optimized algorithms
4. Computes FVC (forced vital capacity) from complete expiration phase
5. Validates parameters against physiological ranges from `references/pitfalls.md`
6. Creates flow-volume loop visualization with annotations
7. Outputs structured JSON results with validation warnings

## Error Handling
The script includes comprehensive error handling for file operations and parameter validation. Directory creation errors are handled by ensuring parent directories exist before file operations. Performance issues with large datasets are handled through optimized calculations and plot downsampling. Validation errors catch physiologically impossible values and warn about abnormal ranges.

## Common Pitfalls
- File creation failures due to missing directories
- Incorrect flow patterns during synthetic data generation
- Performance degradation with large datasets
- Unrealistic parameter calculations from improper phase identification

## Output Format
- PNG plot file showing flow-volume loop with annotations
- JSON results file containing FEV1, FVC, ratio, and validation results
- Console logging with parameter values and validation warnings
