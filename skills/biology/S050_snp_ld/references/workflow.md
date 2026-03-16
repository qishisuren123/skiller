1. Prepare genotype data in tab-separated format with individuals as rows and SNPs as columns
2. Ensure SNP column headers follow "chromosome:position" format (e.g., "1:12345")
3. Encode genotypes as 0 (homozygous reference), 1 (heterozygous), 2 (homozygous alternate), -1 (missing)
4. Run the analysis tool: `python scripts/main.py input_genotypes.txt output_dir/`
5. Optionally adjust parameters: --max_distance for genomic window, --r2_threshold, --dprime_threshold, --lod_threshold
6. Tool parses SNP positions and filters pairs by chromosome and distance constraints
7. EM algorithm estimates haplotype frequencies to resolve phase ambiguity in double heterozygotes
8. Calculate linkage disequilibrium statistics (D, D', r², LOD scores) for each valid SNP pair
9. Apply significance filters to identify strongly linked SNP pairs meeting all threshold criteria
10. Review output files: ld_results.txt (all pairs) and significant_ld_pairs.txt (filtered pairs)
11. Analyze results for population structure, haplotype blocks, or quality control purposes
