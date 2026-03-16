## Invalid SNP Header Format

**Error**: Tool fails to parse SNP positions from column headers
**Root Cause**: SNP headers not following expected "chromosome:position" format
**Fix**: Ensure all SNP column headers use format like "1:12345" or "chr1:12345", validate input data formatting before analysis

## Insufficient Sample Size

**Error**: Many SNP pairs return None results despite having genotype data
**Root Cause**: Too few individuals with complete genotype data for both SNPs after removing missing values
**Fix**: Increase minimum sample size threshold or improve genotype calling quality, consider imputation for missing data

## EM Algorithm Convergence Issues

**Error**: Haplotype frequency estimation produces unstable or invalid results
**Root Cause**: Poor initialization or numerical instability in EM algorithm for phase resolution
**Fix**: Implement better starting values based on marginal allele frequencies, add convergence diagnostics and maximum iteration limits

## Memory Exhaustion with Large Datasets

**Error**: Process killed or extremely slow performance with genome-wide data
**Root Cause**: Analyzing all pairwise combinations creates O(n²) memory and computation requirements
**Fix**: Implement chunking strategy to process SNPs in blocks, add distance-based filtering before pairwise analysis, consider parallel processing
