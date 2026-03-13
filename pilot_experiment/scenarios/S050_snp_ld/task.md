# SNP Linkage Disequilibrium Analysis

Create a command-line tool that computes linkage disequilibrium (LD) statistics between pairs of Single Nucleotide Polymorphisms (SNPs) from genotype data.

Your script should accept genotype data in a tab-separated format where rows represent individuals and columns represent SNP positions. Each genotype is encoded as 0 (homozygous reference), 1 (heterozygous), or 2 (homozygous alternate). The script should compute pairwise LD statistics and identify SNP pairs in strong linkage disequilibrium.

## Requirements

1. **Data Processing**: Parse the input genotype matrix and handle missing data (encoded as -1) by excluding individuals with missing genotypes for either SNP in a pair from that pair's calculation.

2. **LD Computation**: Calculate three key LD statistics for each SNP pair:
   - D' (normalized linkage disequilibrium coefficient)
   - r² (squared correlation coefficient)  
   - LOD score (logarithm of odds for linkage)

3. **Distance-based Analysis**: Only compute LD for SNP pairs within a specified maximum distance (in base pairs). SNP positions should be extracted from column headers formatted as "chr:position".

4. **Statistical Filtering**: Identify and output SNP pairs that meet significance criteria: r² ≥ 0.8, |D'| ≥ 0.8, and LOD ≥ 3.0.

5. **Haplotype Frequency Estimation**: For each significant SNP pair, estimate the four possible haplotype frequencies (00, 01, 10, 11) using the expectation-maximization (EM) algorithm when phase information is unavailable.

6. **Output Generation**: Generate two output files:
   - A comprehensive results file with all computed statistics for SNP pairs meeting distance criteria
   - A summary file containing only significant SNP pairs with their haplotype frequencies

Use argparse to handle command-line arguments for input file, output directory, maximum distance threshold, and any other necessary parameters.
