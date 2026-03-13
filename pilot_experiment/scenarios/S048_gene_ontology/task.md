# Gene Ontology Enrichment Analysis

Create a command-line tool that performs Gene Ontology (GO) enrichment analysis on a list of genes. The script should map genes to GO terms and calculate enrichment statistics to identify overrepresented biological processes.

## Requirements

1. **Input Processing**: Accept a list of gene IDs and a background gene set through command-line arguments. The tool should handle both space-separated and comma-separated gene lists.

2. **GO Term Mapping**: Map input genes to their associated GO terms using a synthetic gene-to-GO annotation database. Each gene can be associated with multiple GO terms, and each GO term should have a descriptive name.

3. **Enrichment Calculation**: For each GO term present in the input gene list, calculate:
   - Number of input genes associated with the term
   - Total number of background genes associated with the term
   - Enrichment ratio (observed/expected frequency)
   - Fisher's exact test p-value for statistical significance

4. **Statistical Correction**: Apply Bonferroni correction to adjust p-values for multiple testing correction.

5. **Results Filtering**: Filter results to show only GO terms with at least 2 genes from the input list and corrected p-value < 0.05.

6. **Output Generation**: Save results to a JSON file containing GO term ID, description, gene count, background count, enrichment ratio, raw p-value, and corrected p-value, sorted by corrected p-value.

## Command Line Interface
