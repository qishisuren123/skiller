1. Load CSV data with field observations using pandas.read_csv()
2. Convert date column to datetime format and sort by field_id and date
3. Calculate daily growing degree days using vectorized numpy operations
4. Compute cumulative GDD per field using groupby transform
5. Aggregate all field statistics in single groupby operation for performance
6. Handle NaN values from single-observation fields by setting std to 0.0
7. Find peak NDVI dates using vectorized operations to avoid index issues
8. Create correlation matrix using pandas corr() method with NaN handling
9. Generate summary statistics with top 3 yield correlates
10. Save three output files: features CSV, correlation CSV, and summary JSON
11. Log processing time and key statistics for monitoring
