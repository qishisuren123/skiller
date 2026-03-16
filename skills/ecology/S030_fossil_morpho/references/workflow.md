1. Prepare input CSV file with required columns: specimen_id, taxon, length_mm, width_mm, height_mm, mass_g, formation, epoch
2. Run the script: `python scripts/main.py --input data.csv --output results/`
3. Script loads data and reports specimen count and missing values
4. Data validation identifies and handles non-positive measurements
5. Shape indices computed with division-by-zero protection using np.where()
6. Memory-efficient PCA performed using sklearn StandardScaler and PCA classes
7. PC scores added to main dataframe, with NaN for specimens with missing measurements
8. Group statistics computed by taxon and epoch for all numeric variables
9. Three output files generated: morphometrics.csv, pca_results.csv, taxon_summary.json
10. Console summary displays key metrics including specimen counts and PCA variance explained
