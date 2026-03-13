Write a Python CLI script to process gene expression data with associated sequence information.

Input files:
- expression.csv: rows=samples, columns=genes, values=expression levels (TPM)
- sequences.fasta: gene sequences in FASTA format (>GENE_NAME\nSEQUENCE)

Requirements:
1. Use argparse: --expression CSV, --fasta FASTA, --output directory
2. Read expression matrix; filter out genes with mean TPM < 1 across samples
3. Quantile normalize the expression matrix across samples
4. Parse FASTA file to get sequence lengths per gene
5. Output to directory: normalized_expression.csv, gene_stats.csv (gene_name, mean_tpm, std_tpm, seq_length)
6. Print summary: samples, genes before/after filter, correlation between expression and sequence length
