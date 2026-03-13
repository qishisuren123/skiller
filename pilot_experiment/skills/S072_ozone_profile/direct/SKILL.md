# Atmospheric Ozone Profile Analysis

## Overview
This skill processes vertical ozone profiles from ozonesonde balloon measurements to extract key atmospheric parameters including tropopause identification, column integrations, and stratospheric characterization with quality control and visualization outputs.

## Workflow
1. **Data Ingestion & Quality Control**: Load ozonesonde data (altitude, pressure, temperature, ozone) and apply quality filters to remove negative or unrealistic ozone values (>20 mPa default)
2. **Tropopause Detection**: Calculate temperature lapse rates and identify tropopause height using the WMO thermal definition (lapse rate <2 K/km over 2 km layer)
3. **Column Integration**: Compute tropospheric ozone column (surface to tropopause) and stratospheric column (tropopause to 30 km) using trapezoidal integration with unit conversion
4. **Stratospheric Analysis**: Locate ozone maximum altitude and concentration above tropopause, then calculate scale height by exponential fitting in lower stratosphere
5. **Statistical Summary**: Generate JSON output with all derived parameters including tropopause height, column amounts, ozone maximum properties, and scale height
6. **Profile Visualization**: Create publication-quality altitude vs ozone concentration plot with marked tropopause and ozone maximum
7. **Output Generation**: Save statistical summary as JSON and profile plot as PNG with proper atmospheric science formatting

## Common Pitfalls
- **Incomplete altitude coverage**: Ensure data extends sufficiently into stratosphere (>25 km) for reliable tropopause detection and column calculations
- **Unit conversion errors**: Ozone concentrations in mPa must be converted to Dobson Units (DU) for column integration using proper conversion factors and pressure weighting
- **Tropopause misidentification**: Apply minimum altitude constraint (>6 km) and verify lapse rate calculation uses proper altitude intervals to avoid surface inversions
- **Scale height fitting issues**: Restrict exponential fitting to appropriate altitude range (tropopause+5 to +15 km) and handle cases where insufficient stratospheric data exists
- **Missing data interpolation**: Handle gaps in vertical profiles carefully, especially near tropopause region where small altitude differences significantly impact column calculations

## Error Handling
- Validate input data completeness and altitude ordering before processing
- Implement fallback tropopause detection methods if primary lapse rate method fails
- Check for sufficient data points in stratosphere before attempting scale height calculations
- Handle numerical integration edge cases with proper boundary condition checks
- Provide informative error messages for common data quality issues and processing failures

## Quick Reference
