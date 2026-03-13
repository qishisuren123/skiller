# Phylogenetic Distance Calculator

## Overview
This skill helps create a command-line tool for computing pairwise phylogenetic distances from multiple sequence alignments using standard evolutionary distance metrics including Hamming, Jukes-Cantor, and p-distance calculations.

## Workflow
1. **Parse input arguments** - Handle command-line arguments for alignment file, distance method, and output format options
2. **Load and validate sequences** - Parse FASTA format alignment data and validate sequence lengths are equal
3. **Preprocess alignment** - Extract sequence identifiers and convert sequences to uppercase for consistent processing
4. **Calculate pairwise distances** - Apply selected distance metric to all sequence pairs, handling gaps appropriately
5. **Generate distance matrix** - Create symmetric matrix with sequence names as headers and save as tab-separated file
6. **Export pairwise results** - Output all pairwise distances in JSON format with sequence pair identifiers
7. **Compute summary statistics** - Calculate mean, standard deviation, minimum and maximum distances across all pairs

## Common Pitfalls
- **Jukes-Cantor overflow**: When 4p/3 ≥ 1, the logarithm becomes undefined - fallback to uncorrected p-distance instead of crashing
- **Gap handling inconsistency**: Don't exclude entire columns with gaps - handle gaps on a pairwise basis to maximize data usage
- **Sequence length validation**: Unequal sequence lengths indicate invalid alignment - validate before processing to avoid index errors
- **Ambiguous nucleotide codes**: Standard codes like 'N', 'R', 'Y' should be treated as unknown rather than causing comparison errors
- **Zero distance edge case**: When sequences are identical, ensure Jukes-Cantor returns 0.0 rather than attempting log(1) calculation

## Error Handling
- Validate alignment integrity by checking all sequences have equal length
- Handle mathematical edge cases in Jukes-Cantor correction with fallback to p-distance
- Gracefully handle empty or malformed FASTA input with informative error messages
- Check for minimum of 2 sequences before attempting pairwise calculations

## Quick Reference
