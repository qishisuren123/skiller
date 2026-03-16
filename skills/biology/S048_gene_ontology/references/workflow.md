1. Prepare input gene list in comma or space-separated format
2. Optionally prepare GO annotations file in tab-separated format (gene_id\tgo_term\tdescription)
3. Run the script with required parameters: python main.py --genes "GENE1,GENE2,GENE3"
4. Script loads GO annotations from file or generates synthetic database
5. Parse input genes and background gene set (defaults to all annotated genes)
6. Count GO term occurrences in both input and background sets
7. For each GO term with ≥2 input genes, construct 2x2 contingency table
8. Apply statistical test (Fisher's exact or chi-square approximation)
9. Calculate enrichment ratio as observed/expected frequency
10. Apply Bonferroni correction for multiple testing
11. Filter results by corrected p-value < 0.05
12. Sort by statistical significance and save to JSON file
13. Display summary statistics and top enriched terms
