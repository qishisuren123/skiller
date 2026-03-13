# Weather Front Detection from Temperature Gradient Analysis

## Overview
This skill enables detection of weather fronts by analyzing spatial temperature gradients in atmospheric data. It identifies boundaries between air masses by computing temperature gradients, applying thresholds, and segmenting connected regions into meteorologically significant front structures.

## Workflow
1. **Load atmospheric data** from HDF5 file containing temperature grids, coordinates, and spatial metadata
2. **Apply Gaussian smoothing** to temperature field to reduce measurement noise while preserving front structures
3. **Calculate temperature gradients** in both spatial directions using central differences, converting to physical units (°C/km)
4. **Compute gradient magnitude** and apply threshold to identify potential front locations
5. **Segment connected regions** using morphological operations to group adjacent high-gradient pixels
6. **Filter front segments** by minimum length requirement and calculate meteorological properties
7. **Generate outputs** including JSON metadata and visualization plot with temperature field and detected fronts

## Common Pitfalls
- **Incorrect gradient scaling**: Forgetting to convert gradient units from °C/grid_point to °C/km using the grid_spacing parameter
- **Edge effects in gradients**: Not handling array boundaries properly when computing central differences, leading to artifacts at data edges
- **Over-smoothing temperature data**: Using excessive Gaussian smoothing that removes genuine meteorological front structures
- **Coordinate system confusion**: Mixing up x/y directions with lon/lat when computing gradients, especially in different hemispheres
- **Connected component labeling errors**: Not properly handling diagonal connectivity when segmenting front regions

## Error Handling
- Validate HDF5 file structure and required datasets before processing
- Check for NaN/invalid values in temperature data and handle with masking
- Ensure gradient threshold and smoothing parameters are physically reasonable
- Verify output directory exists and is writable before processing
- Handle edge cases where no fronts are detected above threshold

## Quick Reference
