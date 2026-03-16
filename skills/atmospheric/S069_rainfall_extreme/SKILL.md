---
name: rainfall_extreme
description: "# Rainfall Return Period Analysis

Create a CLI script that analyzes daily precipitation data to compute rainfall return periods and identify extreme precipitation events.

Your script should accept daily precipitation data as comma-separated values, calculate annual maximum series, compute return periods using Weibull plotting position, and identify extreme events exceeding the 10-year return period threshold through linear interpolation or extrapolation."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: atmospheric
---

# Rainfall Extreme

## Overview
This skill creates a CLI tool for rainfall return period analysis using the annual maximum series method. It processes daily precipitation data to calculate return periods, interpolates thresholds for specific return periods, and identifies extreme precipitation events. The tool handles data parsing robustly and provides comprehensive JSON output with statistics.

## When to Use
- Analyzing historical precipitation data for extreme event identification
- Computing return periods for flood risk assessment
- Climate data analysis requiring threshold-based event detection
- Hydrological studies needing annual maximum series analysis
- Environmental monitoring applications

## Inputs
- Daily precipitation data as comma-separated values (handles whitespace/newlines)
- Starting year for the time series (default: 2000)
- Output JSON file path
- Optional: custom return period targets

## Workflow
1. Execute scripts/main.py with precipitation data and output path
2. Script parses input data robustly, handling formatting issues
3. Groups data by year and extracts annual maxima (requires ≥300 days/year)
4. Calculates return periods using Weibull plotting position formula
5. Interpolates or extrapolates 10-year return period threshold
6. Identifies all extreme events exceeding the threshold
7. Computes summary statistics and exports to JSON
8. Refer to references/pitfalls.md for common error patterns

## Error Handling
The system includes comprehensive error handling for data parsing issues, JSON serialization problems, and interpolation edge cases. It gracefully handles missing data, converts NumPy types to native Python types to avoid JSON errors, and provides fallback values when interpolation fails. The robust parsing handles whitespace, newlines, and invalid values by treating them as missing data.

## Common Pitfalls
- JSON serialization errors with NumPy data types - convert to native Python types
- Incorrect threshold logic - higher return periods correspond to higher precipitation values
- Poor data parsing - implement robust cleaning for whitespace and formatting issues
- Insufficient data for interpolation - use extrapolation when target exceeds available range

## Output Format
JSON file containing annual_maxima (year: max_precipitation), return_periods (year: {value, return_period}), extreme_events (date and precipitation for events exceeding threshold), statistics (mean/std of annual maxima, 95th percentile), and calculated 10-year threshold value.
