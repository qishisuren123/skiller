# Estuarine Salinity Gradient Analysis from CTD Transects

## Overview
This skill enables analysis of estuarine salinity gradients using CTD transect data to identify mixing zones, calculate stratification indices, detect haloclines, and map salt wedge intrusion patterns in coastal environments.

## Workflow
1. **Load and validate CTD transect data** - Parse JSON input containing station positions, depths, temperature, salinity, and conductivity measurements
2. **Apply quality control filters** - Flag suspicious salinity jumps >2 PSU and density inversions >0.1 kg/m³ between adjacent measurements
3. **Detect haloclines** - Identify depth ranges where salinity gradient exceeds 0.5 PSU/m over minimum 2m intervals
4. **Calculate stratification parameters** - Compute Simpson's Parameter (Φ) and classify stations as well-mixed, partially mixed, or stratified
5. **Map salt wedge intrusion** - Track 2 PSU isohaline position and calculate penetration distance from river mouth
6. **Analyze tidal mixing efficiency** - Compute Richardson numbers and mixing efficiency parameter η to identify active mixing zones
7. **Generate interpolated salinity field** - Create 2D optimal interpolation on regular grid with appropriate decorrelation scales

## Common Pitfalls
- **Incorrect density calculation**: Use UNESCO equation of state for seawater density, not linear approximation - temperature and pressure effects are critical in estuaries
- **Halocline detection in noisy data**: Apply 3-point running mean before gradient calculation to avoid false positives from instrument noise
- **Salt wedge tracking errors**: Interpolate between measurement depths to find exact 2 PSU crossing, don't just use nearest measurement
- **Stratification parameter units**: Ensure consistent units (J/m³) when integrating Simpson's parameter - depth must be in meters, density in kg/m³
- **Tidal phase confusion**: Account for flood vs ebb tide conditions when interpreting mixing efficiency - same location can show vastly different stratification

## Error Handling
- Validate input data ranges (salinity 0-40 PSU, temperature -2 to 35°C, reasonable lat/lon bounds)
- Handle missing data points using linear interpolation only within 5m depth gaps
- Check for monotonic depth increases and flag reversed profiles
- Gracefully handle cases where haloclines or salt wedge are not detected (output empty arrays with metadata)
- Verify sufficient data density for interpolation (minimum 3 stations per transect)

## Quick Reference
