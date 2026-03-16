---
name: snp_ld
description: "# SNP Linkage Disequilibrium Analysis

Create a command-line tool that computes linkage disequilibrium (LD) statistics between pairs of Single Nucleotide Polymorphisms (SNPs) from genotype data.

Your"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: biology
---

# SNP Linkage Disequilibrium Analysis

## Overview
This skill creates a command-line tool for analyzing linkage disequilibrium (LD) between SNP pairs from genotype data. It computes D', r², and LOD scores using the EM algorithm to handle phase ambiguity, filters pairs by genomic distance, and identifies statistically significant associations.

## When to Use
- Analyzing population genetics data to identify SNP associations
- Quality control in GWAS studies to detect correlated markers
- Fine-mapping disease loci by examining local LD structure
- Population structure analysis and haplotype block identification
- Validating genotype imputation accuracy

## Inputs
- **Genotype file**: Tab-separated format with individuals as rows, SNPs as columns
- **SNP headers**: Format "chr:position" (e.g., "1:12345")
- **Genotype encoding**: 0=homozygous reference, 1=heterozygous, 2=homozygous alternate, -1=missing
- **Distance threshold**: Maximum bp distance between SNP pairs to analyze
- **Significance thresholds**: r², D', and LOD score cutoffs

## Workflow
1. Execute `scripts/main.py` with input genotype file and output directory
2. Parse SNP positions from column headers using chromosome:position format
3. Filter SNP pairs by same chromosome and distance threshold
4. Apply EM algorithm to resolve haplotype phase ambiguity
5. Calculate LD statistics (D, D', r², LOD scores) for each valid pair
6. Identify significant pairs meeting all threshold criteria
7. Output comprehensive results and filtered significant associations
8. Consult `references/pitfalls.md` for common error patterns and solutions

## Error Handling
The tool implements robust error handling for data quality issues. It will handle missing genotype data by excluding incomplete observations, validate SNP header formats and error on malformed position strings, skip monomorphic SNPs that cannot contribute to LD calculations, and handle numerical instabilities in EM algorithm convergence. File I/O errors are caught and logged with descriptive messages to help users identify and resolve input data problems.

## Common Pitfalls
- Incorrect genotype encoding leading to invalid allele frequency calculations
- Missing chromosome/position information in SNP headers causing parsing failures
- Insufficient sample sizes resulting in unreliable LD estimates
- Phase ambiguity in double heterozygotes requiring EM algorithm convergence
- Memory issues with large datasets when analyzing all pairwise combinations

## Output Format
- **ld_results.txt**: All SNP pairs with D, D', r², LOD scores, distances, sample sizes
- **significant_ld_pairs.txt**: Filtered pairs meeting significance thresholds
- Tab-separated format with columns: SNP1, SNP2, chr, pos1, pos2, distance, D, D_prime, r_squared, lod_score, sample_size
- Haplotype frequencies (p00, p01, p10, p11) included for detailed analysis
