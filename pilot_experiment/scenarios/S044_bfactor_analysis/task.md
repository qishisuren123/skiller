# B-Factor Analysis Tool

Create a command-line tool that analyzes B-factor (temperature factor) distributions in protein structures and identifies flexible regions. B-factors indicate atomic displacement and are commonly used to assess protein flexibility and structural reliability.

Your script should accept synthetic B-factor data and perform statistical analysis to identify regions of high flexibility (high B-factors) and generate summary reports.

## Requirements

1. **Data Input**: Accept B-factor values via command-line argument as a comma-separated string, where each value represents the average B-factor for a residue position.

2. **Statistical Analysis**: Calculate basic statistics including mean, median, standard deviation, and quartiles of the B-factor distribution.

3. **Flexible Region Identification**: Identify residues with B-factors above the 75th percentile as "flexible regions" and group consecutive flexible residues into segments.

4. **Normalization**: Provide an option to normalize B-factors to a 0-100 scale based on the min-max values in the dataset.

5. **Output Generation**: Save results to a JSON file containing:
   - Statistical summary (mean, median, std, quartiles)
   - List of flexible residue positions
   - Flexible segments (start-end ranges)
   - Normalized B-factors (if requested)

6. **Visualization**: Generate a simple line plot showing B-factor values by residue position, highlighting flexible regions, and save as PNG.

## Command-line Interface
