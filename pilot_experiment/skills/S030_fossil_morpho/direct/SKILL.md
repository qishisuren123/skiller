# Fossil Morphometric Analysis

## Overview
This skill enables comprehensive morphometric analysis of fossil specimen measurements, including shape index calculations, principal component analysis with eigen-decomposition, and taxonomic/temporal grouping statistics for paleontological research.

## Workflow
1. Parse command-line arguments for input CSV path and output directory using argparse
2. Load and validate fossil specimen data with required columns (specimen_id, taxon, length_mm, width_mm, height_mm, mass_g, formation, epoch)
3. Calculate morphometric shape indices: elongation, flatness, Krumbein sphericity, ellipsoidal volume, and density
4. Perform PCA on standardized measurements using numpy eigen-decomposition of covariance matrix
5. Compute grouped statistics (mean, std) by taxon and epoch for all measurements and indices
6. Export results to three files: enhanced specimen data CSV, PCA components CSV, and summary statistics JSON
7. Print analysis summary with specimen counts, taxa diversity, and PCA variance explanation

## Common Pitfalls
- **Missing measurement validation**: Always check for negative values or zeros in dimensions before calculating shape indices, as these indicate measurement errors
- **Volume unit conversion errors**: Remember to convert mm³ to cm³ (divide by 1000) before calculating density to get g/cm³
- **PCA standardization order**: Apply z-score standardization before computing covariance matrix, not after eigen-decomposition
- **Sphericity formula confusion**: Use the cube root of the product (width × height)^(1/3), not the square root - this is critical for Krumbein sphericity
- **JSON serialization of numpy types**: Convert numpy float64/int64 to Python native types before JSON export to avoid serialization errors

## Error Handling
- Validate CSV structure and required columns before processing
- Handle division by zero in shape calculations by setting invalid results to NaN
- Check for successful eigen-decomposition convergence and handle degenerate covariance matrices
- Ensure output directory exists or create it before file writing
- Wrap file I/O operations in try-catch blocks with informative error messages

## Quick Reference
