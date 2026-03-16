1. Prepare input CSV file with columns: trial, time, neuron_0, neuron_1, etc.
2. Run the script: `python scripts/main.py --input data.csv --output-dir ./plots/`
3. Script detects CSV format and tries multiple delimiters if needed
4. Data is loaded in chunks to handle large files efficiently
5. Numeric columns are cleaned (commas converted to dots for decimal points)
6. Missing values are handled appropriately for each visualization type
7. Trial-averaged heatmap is generated with proper time axis labeling
8. Population PSTH is calculated using robust statistics (minimum neuron thresholds)
9. Both plots are saved as high-resolution PNG files
10. Data summary statistics are printed to console
11. Memory is cleaned up after each major operation to prevent crashes
12. Check output directory for firing_rate_heatmap.png and population_psth.png
