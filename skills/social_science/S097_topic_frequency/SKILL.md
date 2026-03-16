---
name: topic_frequency
description: "# Topic Frequency Analysis

Create a CLI script that analyzes topic frequency trends from a timestamped document corpus. The script should process synthetic document data and compute how frequently different topics appear over time periods (daily, weekly, monthly). Includes trend analysis using linear regression, statistical summaries, JSON output, and visualizations."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: social_science
---

# Topic Frequency Analysis

## Overview
This skill provides a complete CLI tool for analyzing topic frequency trends in timestamped document collections. It generates synthetic document data with realistic temporal patterns, calculates frequency distributions across configurable time periods, performs statistical trend analysis using linear regression, and outputs comprehensive results in JSON format with visualizations.

## When to Use
- Analyzing research topic evolution in academic corpora
- Tracking content themes in social media or news datasets
- Understanding temporal patterns in document collections
- Generating baseline analyses for topic modeling validation
- Creating synthetic datasets for testing topic analysis pipelines

## Inputs
- `--num-docs`: Number of synthetic documents to generate (default: 1000)
- `--period`: Time aggregation period - daily, weekly, or monthly (default: monthly)  
- `--output`: Output JSON filename (default: topic_analysis.json)

## Workflow
1. Execute scripts/main.py with desired parameters
2. Script generates synthetic documents with temporal bias patterns
3. Documents are aggregated by time period using pandas crosstab for efficiency
4. Linear regression analysis identifies increasing/decreasing/stable trends
5. Statistical summaries calculate most frequent topics and variance metrics
6. Results are serialized to JSON with proper timestamp handling
7. Visualization creates line plots showing frequency trends over time
8. Consult references/pitfalls.md for common error handling patterns

## Error Handling
The script includes robust error handling for JSON serialization issues with pandas Timestamps. When pandas datetime objects cannot be serialized, the system converts them to string format using strftime. The code also handles empty frequency arrays in trend analysis to prevent regression errors. Performance optimization handles large datasets by using efficient pandas operations like crosstab instead of groupby operations.

## Common Pitfalls
- Incorrect scipy.stats function names (linregr vs linregress)
- JSON serialization failures with pandas Timestamp objects
- Performance degradation with large datasets using inefficient groupby operations
- Memory issues when processing daily periods on large document collections

## Output Format
JSON structure with summary_statistics (most frequent topics, variance metrics), trend_analysis (slope, r-squared, p-values, trend classifications), and time_series_data (absolute counts and relative frequencies by time period). PNG visualization file showing topic frequency trends as line plots with proper legends and formatting.
