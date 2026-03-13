# VCF Variant Quality Filter

Create a command-line tool that filters and annotates VCF (Variant Call Format) variant calls based on quality metrics and allele frequencies.

Your script should accept a tab-separated input file containing variant data with the following columns: CHROM, POS, REF, ALT, QUAL, DP (depth), AF (allele frequency), and GT (genotype). The tool should filter variants based on user-specified thresholds and generate both filtered output files and summary statistics.

## Requirements

1. **Argument parsing**: Use argparse to accept input file path, output prefix, quality threshold (--min-qual, default 30), depth threshold (--min-depth, default 10), and allele frequency threshold (--min-af, default 0.05).

2. **Quality filtering**: Filter variants that meet ALL criteria: QUAL >= min_qual, DP >= min_depth, and AF >= min_af. Variants with missing values (represented as '.') in any of these fields should be excluded.

3. **Annotation**: Add three new columns to filtered variants: FILTER_STATUS (PASS/FAIL), QUAL_CATEGORY (HIGH if QUAL >= 50, MEDIUM if 30 <= QUAL < 50, LOW otherwise), and HET_HOM (HET for heterozygous genotypes like "0/1", HOM for homozygous like "0/0" or "1/1").

4. **Output generation**: Create two output files: `{output_prefix}_filtered.tsv` containing only PASS variants with all original columns plus annotation columns, and `{output_prefix}_rejected.tsv` containing FAIL variants with annotations.

5. **Summary statistics**: Generate `{output_prefix}_summary.json` with statistics including total variants processed, number passed/failed, mean quality score of passed variants, and counts by quality category.

6. **Chromosome-specific filtering**: If --chr argument is provided, only process variants from that specific chromosome.

The tool should handle edge cases like empty input files and provide informative error messages for invalid thresholds.
