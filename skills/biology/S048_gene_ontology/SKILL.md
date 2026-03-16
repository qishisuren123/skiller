---
name: gene_ontology
description: "# Gene Ontology Enrichment Analysis

Create a command-line tool that performs Gene Ontology (GO) enrichment analysis on a list of genes. The script should map genes to GO terms and calculate enrichment"
license: MIT
compatibility: "Python >=3.9"
metadata:
  author: skiller-generator
  version: "1.0"
  domain: biology
---

# Gene Ontology Enrichment Analysis

## Overview
This tool performs Gene Ontology (GO) enrichment analysis to identify biological processes, molecular functions, and cellular components that are statistically overrepresented in a given gene set. It supports both synthetic data generation for testing and loading real GO annotations from tab-separated files.

## When to Use
- Analyzing differentially expressed genes from RNA-seq experiments
- Identifying functional themes in gene clusters
- Validating biological hypotheses about gene function
- Comparing functional enrichment between different gene sets

## Inputs
- **Gene list**: Comma or space-separated list of gene identifiers
- **Background genes** (optional): Reference gene set for statistical comparison
- **GO annotations file** (optional): Tab-separated file with gene-to-GO mappings
- **Output file**: JSON file for results storage

## Workflow
1. Execute `scripts/main.py` with gene list and parameters
2. Load GO annotations from file or generate synthetic database
3. Parse input and background gene sets
4. Calculate GO term frequencies in both sets
5. Apply statistical test (Fisher's exact or chi-square approximation)
6. Apply multiple testing correction (Bonferroni)
7. Filter significant results and save to JSON
8. Reference `references/workflow.md` for detailed steps

## Error Handling
The tool includes comprehensive error handling for common issues:
- Missing GO annotation files trigger clear error messages
- Malformed input files are handled gracefully with line-by-line validation
- Statistical test failures fall back to alternative methods
- Empty gene sets and missing genes are properly managed

## Common Pitfalls
- Scipy dependency issues resolved by implementing manual statistical tests
- Contingency table construction errors fixed by proper background/input separation
- Performance bottlenecks addressed with chi-square approximation for large datasets
- See `references/pitfalls.md` for detailed error scenarios and solutions

## Output Format
JSON file containing enriched GO terms with:
- GO term ID and description
- Gene counts in input and background sets
- Enrichment ratio and statistical significance
- Multiple testing corrected p-values
