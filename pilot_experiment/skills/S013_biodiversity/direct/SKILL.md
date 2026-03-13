# Biodiversity Indices Calculator

## Overview
This skill enables calculation of standard biodiversity indices (species richness, Shannon diversity, Simpson diversity, Pielou evenness) from species abundance matrices, handling ecological data processing requirements and zero-abundance edge cases.

## Workflow
1. Parse command line arguments for input CSV, output CSV, and specific indices to calculate
2. Load species abundance matrix using pandas, with sites as rows and species as columns
3. For each site, filter out zero abundances and calculate total abundance and species richness
4. Compute Shannon diversity index (H' = -Σ(pi * ln(pi))) where pi is relative abundance
5. Calculate Simpson diversity (1-D where D = Σ(pi²)) and Pielou evenness (J = H'/ln(S))
6. Generate output DataFrame with site identifiers and all calculated indices
7. Save results to CSV and print ecological summary statistics

## Common Pitfalls
- **Zero abundance handling**: Always filter zeros before log calculations in Shannon index to avoid math domain errors
- **Empty sites**: Sites with no species (all zeros) need special handling - assign richness=0, other indices=0
- **Single species sites**: Pielou evenness becomes undefined (0/0), handle as evenness=0 by convention
- **Column naming**: Ensure species columns are properly identified and site names/indices are preserved
- **Floating point precision**: Use appropriate rounding for ecological interpretation (typically 3-4 decimal places)

## Error Handling
- Validate input CSV exists and has proper structure (numeric abundance data)
- Check for negative abundance values (biologically impossible)
- Handle empty datasets or sites with zero total abundance
- Catch math domain errors in logarithmic calculations
- Provide informative error messages for malformed ecological data

## Quick Reference
