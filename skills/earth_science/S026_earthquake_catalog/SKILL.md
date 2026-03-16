---
name: earthquake_catalog
description: "Write a Python CLI script to analyze an earthquake catalog and identify aftershock sequences.

Input: A CSV file with columns:
- event_id, datetime, latitude, longitude, depth_km, magnitude, mag_type
"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: earth_science
---

# Earthquake Catalog Analysis

## Overview
This skill provides a comprehensive Python CLI tool for analyzing earthquake catalogs and identifying aftershock sequences. It calculates Gutenberg-Richter b-values, estimates magnitude completeness, identifies aftershock clusters using spatiotemporal criteria, and generates magnitude-frequency statistics. The tool is optimized for large datasets (50,000+ events) using vectorized operations.

## When to Use
- Analyzing seismic catalogs for research or monitoring
- Identifying aftershock sequences following major earthquakes
- Computing seismological parameters like b-values and completeness magnitudes
- Processing large earthquake datasets efficiently
- Generating statistical summaries of seismic activity

## Inputs
- CSV file with earthquake catalog data containing columns: event_id, datetime, latitude, longitude, depth_km, magnitude, mag_type
- Clustering parameters: spatial radius (km) and temporal window (hours)
- Output directory path

## Workflow
1. Execute `scripts/main.py` with required arguments
2. Load and validate earthquake catalog data
3. Calculate magnitude completeness using histogram peak method
4. Compute Gutenberg-Richter b-value using Aki formula
5. Identify aftershock sequences using optimized spatiotemporal clustering
6. Generate magnitude-frequency statistics
7. Export results to JSON and CSV files
8. Reference `references/pitfalls.md` for common error patterns and solutions

## Error Handling
The script includes robust error handling for common issues:
- Division by zero errors in b-value calculation are handled by adjusting completeness magnitude
- Non-monotonic histogram bins are prevented using proper floating-point arithmetic
- JSON serialization errors from NumPy types are resolved with type conversion
- Missing or invalid data is logged and handled gracefully

## Common Pitfalls
- B-value calculation fails when completeness magnitude equals mean magnitude
- Histogram binning with floating-point precision can create non-monotonic arrays
- Large datasets cause performance issues with nested loop approaches
- NumPy data types cause JSON serialization failures
- Memory issues with vectorized operations on very large datasets

## Output Format
- `catalog_stats.json`: Summary statistics including b-value, completeness magnitude, largest event details
- `aftershock_sequences.csv`: Identified aftershock pairs with distances, time differences, magnitude differences
- `magnitude_freq.csv`: Magnitude-frequency distribution with cumulative counts and log values
