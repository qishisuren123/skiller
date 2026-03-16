1. Parse command line arguments to determine input method (CSV file or individual values)
2. If using CSV input, load data with pandas and auto-detect column names using common patterns
3. Validate data by removing NaN values and checking array length consistency
4. Bin wind directions into 16 compass sectors using 22.5-degree intervals centered on cardinal directions
5. Classify wind speeds into 4 categories: Calm (0-2 m/s), Light (2-5 m/s), Moderate (5-8 m/s), Strong (8+ m/s)
6. Calculate frequency statistics for each sector-speed combination using numpy array operations
7. Generate comprehensive JSON statistics including sector frequencies, percentages, and mean speeds
8. Create frequency matrix for memory-efficient plotting with large datasets
9. Generate polar bar chart wind rose with stacked speed categories using matplotlib
10. Save outputs and log processing status throughout workflow
