Write a Python CLI script to parse SwissProt protein entries from a JSON file and extract structured information.

Input: A JSON file containing a list of protein entries, each with fields like:
- accession, id, protein.recommendedName, gene, organism, sequence, comments, features

Requirements:
1. Use argparse: --input JSON path, --output CSV path
2. For each protein entry extract: accession, protein_name, gene_name, organism, sequence_length, number_of_features, GO_terms (from dbReferences)
3. Handle missing fields gracefully (use empty string or 0)
4. Output a CSV with one row per protein
5. Print summary: total proteins, organisms count, average sequence length
