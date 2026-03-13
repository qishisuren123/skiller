Write a Python CLI script to calculate biodiversity indices from a species abundance matrix.

Input: A CSV file where rows are sampling sites and columns are species. Values are individual counts.

Requirements:
1. Use argparse: --input CSV, --output CSV, --indices (default "all")
2. For each site calculate: species richness, Shannon diversity (H'), Simpson diversity (1-D), Pielou evenness (J), total abundance
3. Handle zero abundances correctly (skip in log calculations)
4. Output CSV with site_id and all diversity indices as columns
5. Print summary: total sites, total species, mean Shannon diversity, most diverse site
