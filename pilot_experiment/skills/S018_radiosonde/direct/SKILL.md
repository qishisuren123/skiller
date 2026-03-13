# Radiosonde Atmospheric Sounding Analysis

## Overview
Analyzes radiosonde atmospheric profile data to compute key meteorological parameters including environmental lapse rates, tropopause height, CAPE/CIN values, and temperature inversions from CSV sounding data.

## Workflow
1. Parse command line arguments for input CSV file and output directory paths
2. Load and validate radiosonde data with required columns (pressure, temperature, dewpoint, wind_speed, wind_direction, altitude)
3. Calculate environmental lapse rates between consecutive atmospheric levels using the formula: lapse_rate = -(T2 - T1) / ((alt2 - alt1) / 1000)
4. Identify tropopause as the lowest level above 5 km where lapse rate < 2°C/km for at least 2 km depth
5. Compute CAPE and CIN using parcel method: lift surface parcel dry-adiabatically to LCL, then moist-adiabatically, integrating buoyancy energy
6. Detect temperature inversions where temperature increases with altitude and calculate inversion strength
7. Export processed profile CSV with lapse rates and summary JSON with all computed atmospheric parameters

## Common Pitfalls
- **Altitude sorting**: Radiosonde data may not be sorted by altitude - always sort ascending before calculations to ensure proper level-by-level processing
- **Missing data handling**: Atmospheric soundings often have missing values - use pandas dropna() and validate data completeness before computations
- **Unit conversions**: Ensure consistent units throughout - temperatures in Celsius, altitudes in meters, pressures in hPa, and convert properly for lapse rate calculations
- **Tropopause detection edge cases**: Handle cases where tropopause criteria aren't met (e.g., shallow soundings) by returning null values rather than crashing
- **CAPE integration bounds**: Carefully track LCL and LFC levels to separate CIN (below LFC) from CAPE (above LFC) regions during parcel integration

## Error Handling
- Validate input CSV contains all required columns before processing
- Check for sufficient data points (minimum 10 levels) and altitude range coverage
- Handle division by zero in lapse rate calculations when altitude differences are negligible
- Gracefully handle cases where tropopause detection fails by setting null values in output
- Wrap file I/O operations in try-catch blocks with informative error messages

## Quick Reference
