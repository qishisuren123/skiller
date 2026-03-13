# Phylogenetic Distance Calculator

Create a command-line tool that computes pairwise phylogenetic distances from multiple sequence alignments using various distance metrics commonly used in phylogenetic analysis.

Your script should accept a multiple sequence alignment in FASTA format (provided as synthetic data) and calculate evolutionary distances between all pairs of sequences. The tool should support multiple distance calculation methods and output results in both matrix and pairwise formats.

## Requirements

1. **Input Processing**: Parse command-line arguments for input alignment data, distance method, and output options. Accept sequence data either from stdin or as a string argument for testing purposes.

2. **Distance Calculations**: Implement at least three distance metrics:
   - Hamming distance (proportion of differing sites)
   - Jukes-Cantor distance (corrects for multiple substitutions)
   - p-distance (simple proportion of differences, gaps ignored)

3. **Gap Handling**: Properly handle alignment gaps ('-' characters) by excluding gap-containing positions from distance calculations on a pairwise basis.

4. **Matrix Output**: Generate a symmetric distance matrix and save it as a tab-separated file with sequence names as headers and row labels.

5. **Pairwise Output**: Create a JSON file containing all pairwise distances with sequence pair identifiers and their corresponding distance values.

6. **Summary Statistics**: Calculate and output summary statistics including mean distance, standard deviation, minimum and maximum pairwise distances for the dataset.

The Jukes-Cantor correction formula is: d = -3/4 * ln(1 - 4/3 * p), where p is the proportion of differing sites. Handle cases where the correction is undefined (when 4p/3 ≥ 1) by returning the uncorrected p-distance.

Your script should be robust to different sequence lengths and handle standard nucleotide ambiguity codes appropriately.
