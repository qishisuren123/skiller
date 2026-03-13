Write a Python CLI script to compute crop yield prediction features from field observation data.

Input: A CSV file with columns:
- field_id, date (YYYY-MM-DD), ndvi, soil_moisture, temperature, rainfall_mm, crop_type, yield_tons

Requirements:
1. Use argparse: --input CSV path, --output directory, --base-temp (default 10.0 for growing degree days calculation)
2. Compute Growing Degree Days (GDD) per field: for each date, GDD_daily = max(0, temperature - base_temp). Cumulative GDD is the running sum within each field.
3. Aggregate NDVI statistics per field: mean, max, min, std, and the date of peak NDVI
4. Create a feature matrix: one row per field with columns field_id, crop_type, mean_ndvi, max_ndvi, ndvi_std, peak_ndvi_date, total_rainfall, mean_soil_moisture, cumulative_gdd, yield_tons
5. Compute a Pearson correlation matrix among all numeric features (including yield)
6. Output: field_features.csv (the feature matrix), correlation_matrix.csv (features x features), summary.json (n_fields, n_crop_types, feature_names, top_3_yield_correlates)
7. Print summary: number of fields processed, strongest yield correlate
