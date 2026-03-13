# Gene Ontology Enrichment Analysis

## Overview
This skill enables creation of a command-line tool for performing Gene Ontology (GO) enrichment analysis on gene lists. It identifies statistically overrepresented biological processes by mapping genes to GO terms and calculating enrichment statistics with proper multiple testing correction.

## Workflow
1. **Parse command-line arguments** to extract input gene list, background gene set, and output file path
2. **Create synthetic GO annotation database** mapping genes to GO terms with descriptive names
3. **Map input genes to GO terms** and count occurrences for each term in both input and background sets
4. **Calculate enrichment statistics** including observed/expected ratios and Fisher's exact test p-values
5. **Apply Bonferroni correction** to adjust p-values for multiple testing
6. **Filter significant results** based on minimum gene count (≥2) and corrected p-value (<0.05)
7. **Export results to JSON** sorted by statistical significance

## Common Pitfalls
- **Empty intersections**: Input genes may not overlap with background set, leading to no results. Solution: Validate gene overlap and provide informative error messages.
- **Fisher's exact test parameters**: Incorrect contingency table construction can give wrong p-values. Solution: Carefully construct 2x2 table with proper counts for genes in/out of term and input/background sets.
- **Multiple testing explosion**: Too many GO terms can make Bonferroni correction overly conservative. Solution: Pre-filter GO terms by minimum representation before correction.
- **Gene ID case sensitivity**: Mismatched case between input and database can cause mapping failures. Solution: Normalize all gene IDs to uppercase for consistent matching.
- **Zero background counts**: GO terms with no background genes cause division errors. Solution: Skip terms with zero background representation during enrichment calculation.

## Error Handling
- Validate that input and background gene lists are non-empty and contain valid identifiers
- Check for sufficient overlap between input genes and GO annotation database
- Handle cases where no GO terms meet significance thresholds by providing informative output
- Catch and report file I/O errors during JSON output generation
- Implement graceful handling of statistical edge cases (zero counts, perfect enrichment)

## Quick Reference
