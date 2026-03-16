1. Parse command-line arguments including B-factor values, output file, normalization flag, and plot prefix
2. Convert comma-separated B-factor string into list of float values using parse_bfactors()
3. Calculate comprehensive statistics using numpy: mean, median, standard deviation, quartiles, min/max
4. Determine flexibility threshold as 75th percentile of B-factor distribution
5. Identify flexible residues by comparing each B-factor value against threshold
6. Group consecutive flexible residues into contiguous segments using group_consecutive_segments()
7. Generate matplotlib visualization showing B-factor line plot with highlighted flexible regions
8. Add colored spans for each flexible segment and threshold line to plot
9. Save plot as PNG file with high resolution (300 DPI)
10. Compile results dictionary with statistics, flexible residues, segments, and threshold
11. Apply normalization to 0-100 scale if --normalize flag is specified
12. Save analysis results to JSON file with proper type conversion for serialization
13. Display summary information including segment details to console
