Write a Python CLI script to perform morphometric analysis on fossil specimen measurements.

Input: A CSV file with columns:
- specimen_id, taxon, length_mm, width_mm, height_mm, mass_g, formation, epoch

Requirements:
1. Use argparse: --input CSV path, --output directory
2. Compute shape indices for each specimen:
   - Elongation = length_mm / width_mm
   - Flatness = width_mm / height_mm
   - Sphericity = (width_mm * height_mm) ^ (1/3) / length_mm  (Krumbein sphericity approximation)
   - Estimated volume = (4/3) * pi * (length_mm/2) * (width_mm/2) * (height_mm/2) as ellipsoid
   - Density = mass_g / volume (convert mm^3 to cm^3 first)
3. Perform PCA on the 4 measurement columns (length, width, height, mass) after z-score standardization. Use numpy eigen-decomposition of covariance matrix. Report PC1-PC4 loadings and explained variance ratios.
4. Group statistics by taxon and by epoch: mean, std of all measurements and shape indices
5. Output: morphometrics.csv (original columns + shape indices + PC scores), pca_results.csv (component, explained_variance_ratio, length_loading, width_loading, height_loading, mass_loading), taxon_summary.json (per taxon: n_specimens, mean/std of each measurement and shape index; per epoch: same)
6. Print summary: number of specimens, number of taxa, dominant taxon, PCA variance explained by first 2 components
