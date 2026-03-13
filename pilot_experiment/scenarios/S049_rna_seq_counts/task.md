# RNA-seq Count Matrix Normalization

Create a command-line tool that normalizes RNA-seq count matrices using TPM (Transcripts Per Million) and DESeq2-style normalization methods.

Your script should accept raw count matrices and gene length information to produce normalized expression values that account for both sequencing depth and gene length biases commonly found in RNA-seq data.

## Requirements

1. **Input Processing**: Accept a count matrix (genes × samples) and gene lengths via command-line arguments. The count matrix should contain integer counts, and gene lengths should be in base pairs.

2. **TPM Normalization**: Calculate TPM values for each gene in each sample using the standard formula: TPM = (counts / gene_length) × 1e6 / sum(counts / gene_length). This accounts for both gene length and library size.

3. **DESeq2-style Normalization**: Implement size factor normalization similar to DESeq2: calculate geometric mean of counts for each gene across samples, compute size factors as median of ratios, then normalize counts by dividing by sample-specific size factors.

4. **Quality Metrics**: Calculate and report normalization quality metrics including the coefficient of variation of library sizes before and after normalization, and correlation between original and normalized data.

5. **Output Generation**: Save normalized matrices to separate CSV files (TPM and DESeq2-style), and generate a JSON summary containing normalization statistics, library sizes, and size factors.

6. **Visualization**: Create a comparison plot showing library size distributions before and after normalization, saved as a PNG file.

Use argparse to handle command-line arguments for input/output file paths and any optional parameters like minimum count thresholds.
