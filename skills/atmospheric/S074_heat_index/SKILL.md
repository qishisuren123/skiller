---
name: heat_index
description: "# Heat Index Analysis and Heat Wave Detection

Create a CLI script that processes atmospheric temperature and humidity data to calculate heat index time series and identify heat wave events with statistical analysis."
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: atmospheric
---

# Heat Index Analysis and Heat Wave Detection

## Overview
This skill provides a comprehensive CLI tool for calculating heat indices from temperature and humidity data and detecting heat wave events using climatological baselines. It implements the full National Weather Service heat index formula with adjustments, establishes rolling 30-year baselines with 15-day windows, and identifies heat wave events based on statistical thresholds.

## When to Use
- Processing weather station data for heat stress analysis
- Climate research requiring heat index calculations
- Public health studies analyzing extreme heat events
- Environmental monitoring and early warning systems
- Historical climate analysis and trend detection

## Inputs
- Temperature data file (CSV) with columns: 'date'/'datetime' and 'temp_f'/'temperature'
- Humidity data file (CSV) with columns: 'date'/'datetime' and 'rh_percent'/'humidity'
- Baseline years for climatology (default: 30)
- Percentile threshold for heat waves (default: 90th percentile)
- Minimum heat wave duration in days (default: 3)

## Workflow
1. Execute `scripts/main.py` with temperature and humidity data files
2. Script loads and merges data on datetime, handling flexible column names
3. Calculate heat index using full NWS formula with humidity adjustments
4. Establish climatological baseline using rolling 15-day window approach
5. Detect heat wave events as consecutive threshold exceedances
6. Merge events separated by single days and calculate statistics
7. Output time series with thresholds and heat wave event summaries
8. Reference `references/workflow.md` for detailed processing steps

## Error Handling
The script includes comprehensive error handling for common data issues. It validates column names and provides clear error messages when required columns are missing. The merge operation handles mismatched datetime formats gracefully, and the baseline calculation manages insufficient data periods appropriately.

## Common Pitfalls
- Column name mismatches between expected and actual data formats
- Pandas merge errors when combining datasets with different structures
- Insufficient historical data for reliable baseline calculations
- Missing data gaps affecting heat wave event continuity

## Output Format
- Time series CSV: datetime, temperature, humidity, heat_index, threshold
- Heat wave JSON: events array with start/end dates, duration, statistics
- Summary statistics: total events, heat wave days, intensity metrics
