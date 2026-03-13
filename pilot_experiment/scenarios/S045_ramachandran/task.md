# Ramachandran Plot Analysis Tool

Create a CLI tool that generates synthetic protein backbone dihedral angle data, creates Ramachandran plots, and identifies structural outliers.

The Ramachandran plot is a fundamental tool in protein structure analysis that displays the distribution of phi (φ) and psi (ψ) backbone dihedral angles. Most amino acid residues cluster in allowed regions, while outliers may indicate structural problems or unusual conformations.

Your script should accept the following arguments:
- `--num_residues` or `--num-residues`: Number of residues to generate (default: 500)
- `--output_plot` or `--output-plot`: Output PNG file for the Ramachandran plot
- `--output_data` or `--output-data`: Output JSON file containing angle data and analysis
- `--outlier_threshold` or `--outlier-threshold`: Z-score threshold for outlier detection (default: 2.5)

## Requirements:

1. **Generate synthetic dihedral angles**: Create phi and psi angles following realistic distributions. Most should fall in allowed regions (alpha-helix: φ≈-60°, ψ≈-45°; beta-sheet: φ≈-120°, ψ≈+120°), with some random scatter and occasional outliers.

2. **Create Ramachandran plot**: Generate a scatter plot with phi on x-axis (-180° to +180°) and psi on y-axis (-180° to +180°). Color-code points by density or structural region. Include axis labels and title.

3. **Identify outliers**: Use statistical methods (e.g., kernel density estimation or distance-based) to identify residues with unusual phi/psi combinations based on the threshold parameter.

4. **Calculate structural statistics**: Compute the percentage of residues in favored regions (alpha-helix, beta-sheet) and disallowed regions.

5. **Export analysis results**: Save a JSON file containing all phi/psi angles, outlier residue indices, regional percentages, and summary statistics.

6. **Handle edge cases**: Properly handle angle periodicity (-180°/+180° boundary) and validate that outlier thresholds produce reasonable results.
