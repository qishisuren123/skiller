# Biodiversity Indices Calculator CLI

## Overview
This skill helps create a robust Python CLI script for calculating biodiversity indices (Shannon diversity, Simpson diversity, Pielou evenness, species richness) from species abundance data with proper error handling and data validation.

## Workflow
1. **Set up argument parsing** with input/output files and indices selection
2. **Validate input data** for negative values, non-numeric data, and edge cases
3. **Parse indices parameter** to determine which calculations to perform
4. **Calculate indices for each site** using clean, validated data
5. **Handle edge cases** like all-zero sites gracefully
6. **Format output** with proper column ordering (site_id first)
7. **Generate summary statistics** when Shannon diversity is calculated

## Common Pitfalls
- **Shannon diversity calculation bug**: Don't filter zeros before passing to function - filter within function but use original total for proportions
- **Species count interpretation**: Count species actually found across sites, not just number of columns
- **Empty dataset handling**: Check for empty results before calculating summary statistics to avoid KeyError
- **Column ordering**: Explicitly define column order for consistent CSV output with site_id first
- **Edge case handling**: Sites with all zeros or negative values need special handling

## Error Handling
- Validate data for negative values, non-numeric columns, all-zero sites
- Convert negative values to zero with warnings
- Handle division by zero in evenness calculation (richness <= 1)
- Handle empty datasets gracefully in summary statistics
- Provide clear error messages for invalid indices parameters

## Quick Reference
