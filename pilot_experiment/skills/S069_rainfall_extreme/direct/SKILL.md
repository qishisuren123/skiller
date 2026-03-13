# Rainfall Return Period Analysis

## Overview
This skill enables hydrological analysis of daily precipitation data to compute return periods using the annual maximum series method, identify extreme precipitation events, and generate statistical summaries for flood risk assessment and water resource management.

## Workflow
1. **Parse and validate input data**: Convert comma-separated precipitation values to numpy array, handle missing data (negative values), and create date index from start year
2. **Extract annual maxima**: Group daily data by complete calendar years, compute maximum precipitation for each year, excluding incomplete years at dataset boundaries
3. **Calculate return periods**: Sort annual maxima in descending order, assign ranks, and apply Weibull plotting position formula T = (n+1)/r
4. **Determine extreme event threshold**: Find the 10-year return period precipitation value through interpolation of the return period curve
5. **Identify extreme events**: Scan all daily data for events exceeding the 10-year threshold, recording dates and magnitudes
6. **Compute statistical summary**: Calculate mean annual maximum, standard deviation of annual maxima, and 95th percentile of all daily precipitation
7. **Export results**: Structure all outputs into JSON format with annual maxima, return periods, extreme events, and statistics

## Common Pitfalls
- **Incomplete year handling**: Including partial years at dataset boundaries skews return period calculations. Always verify complete calendar years (365/366 days) before extracting annual maxima.
- **Rank assignment errors**: Weibull formula requires ranks starting from 1 for the highest value. Using zero-based indexing or incorrect sorting direction produces invalid return periods.
- **Missing data propagation**: Negative values representing missing data can become false maxima if not filtered before annual maximum extraction.
- **Interpolation boundary issues**: When the 10-year return period falls outside the observed range, linear extrapolation may produce unrealistic thresholds. Validate against physical precipitation limits.
- **Date indexing misalignment**: Incorrect start year or leap year handling can misalign precipitation values with calendar dates, affecting extreme event identification.

## Error Handling
- Validate input data length matches expected time series duration
- Check for sufficient complete years (minimum 10) for meaningful return period analysis
- Handle edge cases where no events exceed the 10-year threshold
- Implement bounds checking for interpolation and warn about extrapolation
- Gracefully handle file I/O errors with informative messages

## Quick Reference
