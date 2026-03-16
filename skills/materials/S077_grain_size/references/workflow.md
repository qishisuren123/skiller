1. Prepare grain diameter measurements from microscopy analysis in micrometers
2. Execute the script with required --diameters parameter containing comma-separated values
3. Optionally provide --density parameter for specific surface area calculation
4. Script validates and cleans input data by removing NaN, zero, negative, and infinite values
5. Calculate basic statistical measures (mean, median, standard deviation, min, max, count)
6. Compute distribution percentiles D10, D30, D50, D60, D90 using numpy percentile function
7. Calculate uniformity coefficient (Cu = D60/D10) and curvature coefficient (Cc = D30²/(D60×D10))
8. Classify grains into size categories: fine (<50μm), medium (50-200μm), coarse (>200μm)
9. Generate histogram with explicit bin edges using matplotlib for proper visualization
10. Calculate specific surface area using formula SSA = 6/(ρ × d_mean) with unit conversions
11. Compile all results into structured JSON format with proper data types
12. Save analysis results to specified output file and histogram as PNG image
