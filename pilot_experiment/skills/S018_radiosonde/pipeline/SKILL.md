# Radiosonde Atmospheric Sounding Data Analysis

## Overview
This skill helps create a robust Python CLI script to analyze radiosonde atmospheric sounding data, including lapse rate calculations, tropopause detection, CAPE/CIN calculations, and temperature inversion detection with proper handling of missing data and irregular vertical spacing.

## Workflow
1. **Data Validation**: Check for required columns and remove rows with missing critical data (pressure, temperature, altitude)
2. **Data Sorting**: Sort data by altitude in ascending order to ensure proper vertical profile
3. **Lapse Rate Calculation**: Calculate environmental lapse rates between consecutive levels using the formula: -(T2-T1)/((alt2-alt1)/1000)
4. **Tropopause Detection**: Find lowest level above 5km where lapse rate < 2°C/km with 2km depth coverage
5. **CAPE/CIN Calculation**: Use parcel method with proper dry/moist adiabatic lifting and dewpoint evolution
6. **Inversion Detection**: Identify temperature inversions where temperature increases with altitude
7. **Output Generation**: Create processed CSV and summary JSON with all calculated parameters

## Common Pitfalls
- **Altitude Ordering**: Radiosonde data must be sorted by ascending altitude before lapse rate calculations
- **Lapse Rate Sign Convention**: Use -(T2-T1)/(dz) formula to get positive values for normal atmospheric cooling
- **Tropopause Detection Strictness**: Don't require continuous measurements every few hundred meters; check for adequate vertical coverage instead
- **CAPE Overestimation**: Properly handle dewpoint evolution during dry adiabatic lifting (~2°C/km decrease) and use realistic moist adiabatic rate
- **Missing Data**: Always validate and clean data before calculations; skip NaN values in iterative calculations
- **Surface Layer Effects**: Start buoyancy calculations at least 100m above surface to avoid boundary layer issues

## Error Handling
- Check for required columns before processing
- Validate that critical data (pressure, temperature, altitude) exists
- Handle NaN values in all calculation loops
- Ensure positive altitude differences in lapse rate calculations
- Check for adequate vertical data coverage in tropopause detection
- Handle edge cases like inversions extending to top of sounding

## Quick Reference
