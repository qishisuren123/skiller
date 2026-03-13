# DNA Methylation Beta-Value Analysis and DMR Detection

## Overview
This skill enables analysis of DNA methylation beta-value arrays to identify differentially methylated regions (DMRs) between case and control samples. It processes methylation data across genomic positions, performs statistical testing, and identifies contiguous regions with significant differential methylation patterns.

## Workflow
1. **Load and validate beta-value data** - Import methylation arrays ensuring values are between 0-1 and handle missing data appropriately
2. **Parse genomic coordinates** - Extract chromosome, position, and CpG site information to enable spatial analysis
3. **Filter low-quality probes** - Remove CpG sites with high missing data rates or detection p-values above threshold
4. **Calculate differential methylation statistics** - Perform t-tests or Mann-Whitney U tests between case and control groups for each CpG site
5. **Apply multiple testing correction** - Use Benjamini-Hochberg FDR correction to control for multiple comparisons
6. **Identify contiguous DMRs** - Group adjacent significant CpG sites into regions based on genomic distance and methylation direction
7. **Generate summary report** - Output DMR coordinates, statistics, and visualizations of methylation patterns

## Common Pitfalls
- **Beta-value distribution assumptions**: Beta-values are bounded [0,1] and often bimodal - use non-parametric tests or logit transformation for normality
- **Genomic coordinate sorting**: Always sort CpG sites by chromosome and position before DMR detection to ensure proper adjacency calculations
- **Missing value handling**: High missing rates in methylation data can bias results - filter probes with >20% missing values before analysis
- **DMR boundary definition**: Use both statistical significance and minimum CpG count thresholds to avoid calling single-probe "regions"
- **Chromosome boundary crossing**: Ensure DMR detection doesn't span across different chromosomes by resetting region detection at chromosome boundaries

## Error Handling
- Validate beta-values are in [0,1] range and convert invalid values to NaN
- Check for minimum sample sizes in case/control groups before statistical testing
- Handle chromosome naming inconsistencies (chr1 vs 1) with standardization
- Implement graceful degradation when genomic coordinates are malformed
- Provide informative error messages for common file format issues

## Quick Reference
