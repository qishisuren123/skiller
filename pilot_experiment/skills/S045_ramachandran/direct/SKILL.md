# Ramachandran Plot Analysis Tool

## Overview
Creates a comprehensive protein backbone dihedral angle analysis tool that generates synthetic phi/psi angles, produces publication-quality Ramachandran plots, and identifies structural outliers using statistical methods. This skill combines protein structural biology knowledge with data visualization and statistical analysis.

## Workflow
1. **Parse CLI arguments** and validate input parameters (residue count, thresholds, file paths)
2. **Generate synthetic dihedral angles** using realistic distributions for alpha-helix, beta-sheet, and random coil regions with appropriate scatter
3. **Perform statistical analysis** using kernel density estimation to identify outliers based on local density and z-score thresholds
4. **Create Ramachandran plot** with proper axis scaling (-180° to +180°), density-based coloring, and structural region annotations
5. **Calculate regional statistics** by defining allowed regions and computing occupancy percentages for favored/allowed/disallowed areas
6. **Export comprehensive results** to JSON format including all angles, outlier indices, statistics, and metadata
7. **Handle angle periodicity** correctly at ±180° boundaries and validate all outputs for biological reasonableness

## Common Pitfalls
- **Angle periodicity issues**: Forgetting that -180° and +180° are the same angle can cause artifacts in density estimation and plotting. Solution: Use circular statistics or proper modular arithmetic.
- **Unrealistic angle distributions**: Generating uniform random angles instead of biologically relevant clusters. Solution: Use mixture of Gaussians centered on known secondary structure regions.
- **Density estimation edge effects**: KDE can produce artifacts at plot boundaries. Solution: Use periodic boundary conditions or extend the domain for density calculation.
- **Outlier threshold sensitivity**: Fixed thresholds may not work well for different data sizes. Solution: Validate outlier counts are reasonable (typically 5-15% of residues).
- **Color mapping confusion**: Poor color schemes can make density patterns invisible. Solution: Use perceptually uniform colormaps like 'viridis' or 'plasma'.

## Error Handling
- Validate that outlier thresholds produce reasonable results (1-20% outliers)
- Check for file write permissions before processing data
- Handle edge cases where no outliers are detected or all points are outliers
- Ensure matplotlib backend compatibility for headless environments
- Validate JSON serialization of numpy arrays and handle NaN values

## Quick Reference
