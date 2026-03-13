# Earthquake Catalog Aftershock Analysis

## Overview
This skill helps analyze earthquake catalogs to identify aftershock sequences, compute seismological statistics like the Gutenberg-Richter b-value, and generate comprehensive reports on earthquake clustering patterns.

## Workflow
1. Parse command-line arguments for input CSV, output directory, clustering parameters (radius, time window)
2. Load and validate earthquake catalog data with required columns (event_id, datetime, lat, lon, depth, magnitude)
3. Estimate magnitude of completeness from frequency-magnitude distribution maximum and compute Gutenberg-Richter b-value using Aki's maximum likelihood formula
4. Identify potential mainshocks (magnitude >= 4.0) and search for aftershocks within spatial-temporal clustering criteria using Haversine distance
5. Generate magnitude-frequency statistics with 0.1-magnitude bins including cumulative counts and log10 values
6. Export results to JSON catalog statistics, CSV aftershock sequences, and CSV magnitude-frequency data
7. Print comprehensive summary including total events, b-value, sequence count, and largest event details

## Common Pitfalls
- **Datetime parsing errors**: Earthquake catalogs use various datetime formats. Use pandas.to_datetime() with error handling and consider timezone issues
- **Haversine distance precision**: Earth's radius varies; use 6371.0 km as standard. Ensure latitude/longitude are in decimal degrees, not degrees-minutes-seconds
- **Magnitude completeness estimation**: The histogram maximum method can be noisy for small catalogs. Consider smoothing or minimum event count thresholds (e.g., >= 10 events per bin)
- **Aftershock temporal ordering**: Ensure datetime sorting before sequence identification to avoid missing early aftershocks or incorrect time difference calculations
- **B-value calculation edge cases**: Handle cases where all magnitudes are identical or below completeness threshold, which would cause division by zero in Aki formula

## Error Handling
- Validate CSV columns exist and contain expected data types before processing
- Handle empty or insufficient data gracefully with informative error messages
- Use try-except blocks around mathematical operations (log10, division) that could fail with edge case data
- Check for valid coordinate ranges (latitude: -90 to 90, longitude: -180 to 180) and reasonable depth/magnitude values

## Quick Reference
