#!/usr/bin/env python3
"""
Gene Ontology Enrichment Analysis Tool
Performs GO enrichment analysis on gene lists with statistical significance testing.
"""

import argparse
import json
import sys
from collections import defaultdict
from scipy.stats import fisher_exact
import numpy as np

def create_go_database():
    """Create synthetic gene-to-GO term mapping database."""
    go_database = {
        # Metabolic processes
        'GO:0008152': {
            'name': 'metabolic process',
            'genes': {'GAPDH', 'ALDOA', 'PGK1', 'ENO1', 'PFKM', 'HK1', 'G6PD', 'PGAM1'}
        },
        'GO:0006096': {
            'name': 'glycolytic process', 
            'genes': {'GAPDH', 'ALDOA', 'PGK1', 'ENO1', 'PFKM', 'HK1'}
        },
        'GO:0006006': {
            'name': 'glucose metabolic process',
            'genes': {'GAPDH', 'HK1', 'G6PD', 'PFKM', 'ALDOA'}
        },
        
        # Cell cycle and division
        'GO:0007049': {
            'name': 'cell cycle',
            'genes': {'CCNA2', 'CCNB1', 'CDK1', 'CDK2', 'PCNA', 'MCM2', 'TOP2A'}
        },
        'GO:0000278': {
            'name': 'mitotic cell cycle',
            'genes': {'CCNA2', 'CCNB1', 'CDK1', 'TOP2A', 'PCNA'}
        },
        'GO:0051301': {
            'name': 'cell division',
            'genes': {'CDK1', 'CCNB1', 'TOP2A', 'PCNA', 'MCM2'}
        },
        
        # DNA processes
        'GO:0006260': {
            'name': 'DNA replication',
            'genes': {'PCNA', 'MCM2', 'POLA1', 'RPA1', 'RFC1'}
        },
        'GO:0006281': {
            'name': 'DNA repair',
            'genes': {'BRCA1', 'BRCA2', 'ATM', 'TP53', 'XRCC1', 'PCNA'}
        },
        
        # Protein processes
        'GO:0006412': {
            'name': 'translation',
            'genes': {'RPS6', 'RPL4', 'EIF4E', 'EIF2A', 'RPS3', 'RPL7'}
        },
        'GO:0006508': {
            'name': 'proteolysis',
            'genes': {'CTSD', 'CTSB', 'PSMA1', 'PSMB1', 'UBE2D1'}
        },
        
        # Apoptosis
        'GO:0006915': {
            'name': 'apoptotic process',
            'genes': {'TP53', 'BAX', 'BCL2', 'CASP3', 'CASP9', 'CYTC'}
        },
        
        # Response to stimulus
        'GO:0006950': {
            'name': 'response to stress',
            'genes': {'TP53', 'ATM', 'HSP90AA1', 'HSPA1A', 'BRCA1', 'XRCC1'}
        }
    }
    
    return go_database

def parse_gene_list(gene_string):
    """Parse comma or space-separated gene list."""
    if not gene_string:
        return set()
    
    # Handle both comma and space separation
    genes = gene_string.replace(',', ' ').split()
    return {gene.upper().strip() for gene in genes if gene.strip()}

def get_all_genes_from_database(go_database):
    """Extract all unique genes from GO database."""
    all_genes = set()
    for go_data in go_database.values():
        all_genes.update(go_data['genes'])
    return all_genes

def calculate_go_enrichment(input_genes, background_genes, go_database):
    """Calculate GO term enrichment statistics."""
    results = []
    
    total_input = len(input_genes)
    total_background = len(background_genes)
    
    if total_input == 0 or total_background == 0:
        return results
    
    for go_id, go_data in go_database.items():
        go_genes = go_data['genes']
        
        # Find genes in this GO term
        input_genes_in_term = input_genes & go_genes
        background_genes_in_term = background_genes & go_genes
        
        # Skip if no input genes in this term or insufficient background
        if len(input_genes_in_term) < 2 or len(background_genes_in_term) == 0:
            continue
        
        # Construct contingency table for Fisher's exact test
        a = len(input_genes_in_term)  # input genes in GO term
        b = total_input - a           # input genes not in GO term  
        c = len(background_genes_in_term) - a  # background genes in term (excluding input)
        d = total_background - total_input - c  # background genes not in term (excluding input)
        
        # Skip if invalid contingency table
        if c < 0 or d < 0:
            continue
            
        # Calculate enrichment ratio
        expected_freq = len(background_genes_in_term) / total_background
        observed_freq = a / total_input
        
        if expected_freq > 0:
            enrichment_ratio = observed_freq / expected_freq
        else:
            continue
            
        # Fisher's exact test (one-tailed, testing for over-representation)
        try:
            odds_ratio, p_value = fisher_exact([[a, b], [c, d]], alternative='greater')
        except ValueError:
            continue
            
        results.append({
            'go_id': go_id,
            'go_name': go_data['name'],
            'input_gene_count': a,
            'background_gene_count': len(background_genes_in_term),
            'input_genes': sorted(list(input_genes_in_term)),
            'enrichment_ratio': enrichment_ratio,
            'p_value': p_value
        })
    
    return results

def apply_multiple_testing_correction(results):
    """Apply Bonferroni correction for multiple testing."""
    if not results:
        return results
        
    n_tests = len(results)
    
    for result in results:
        result['corrected_p_value'] = min(1.0, result['p_value'] * n_tests)
    
    return results

def filter_significant_results(results, p_threshold=0.05):
    """Filter results by corrected p-value threshold."""
    return [r for r in results if r['corrected_p_value'] < p_threshold]

def main():
    parser = argparse.ArgumentParser(
        description='Perform Gene Ontology enrichment analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input "TP53,BRCA1,ATM" --background "TP53,BRCA1,ATM,GAPDH,ACTB" --output results.json
  python main.py --input "GAPDH ALDOA PGK1" --output glycolysis_enrichment.json
        """
    )
    
    parser.add_argument('--input', '-i', required=True,
                       help='Input gene list (comma or space separated)')
    parser.add_argument('--background', '-b', 
                       help='Background gene set (comma or space separated). If not provided, uses all genes in GO database')
    parser.add_argument('--output', '-o', default='go_enrichment_results.json',
                       help='Output JSON file (default: go_enrichment_results.json)')
    
    args = parser.parse_args()
    
    # Parse input genes
    input_genes = parse_gene_list(args.input)
    if not input_genes:
        print("Error: No valid input genes provided", file=sys.stderr)
        sys.exit(1)
    
    # Create GO database
    go_database = create_go_database()
    all_database_genes = get_all_genes_from_database(go_database)
    
    # Parse background genes
    if args.background:
        background_genes = parse_gene_list(args.background)
        if not background_genes:
            print("Error: No valid background genes provided", file=sys.stderr)
            sys.exit(1)
    else:
        background_genes = all_database_genes
        print(f"Using all {len(background_genes)} genes from GO database as background")
    
    # Validate gene overlap
    input_in_background = input_genes & background_genes
    if not input_in_background:
        print("Error: No input genes found in background set", file=sys.stderr)
        sys.exit(1)
    
    input_in_database = input_genes & all_database_genes
    if not input_in_database:
        print("Error: No input genes found in GO annotation database", file=sys.stderr)
        sys.exit(1)
    
    print(f"Analyzing {len(input_genes)} input genes against {len(background_genes)} background genes")
    print(f"Found {len(input_in_database)} input genes in GO database")
    
    # Perform enrichment analysis
    results = calculate_go_enrichment(input_genes, background_genes, go_database)
    
    if not results:
        print("No GO terms found with sufficient gene representation")
        sys.exit(0)
    
    # Apply multiple testing correction
    results = apply_multiple_testing_correction(results)
    
    # Filter significant results
    significant_results = filter_significant_results(results)
    
    # Sort by corrected p-value
    significant_results.sort(key=lambda x: x['corrected_p_value'])
    
    # Prepare output
    output_data = {
        'analysis_summary': {
            'input_gene_count': len(input_genes),
            'background_gene_count': len(background_genes),
            'total_go_terms_tested': len(results),
            'significant_go_terms': len(significant_results)
        },
        'input_genes': sorted(list(input_genes)),
        'enriched_go_terms': significant_results
    }
    
    # Save results
    try:
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        print(f"Results saved to {args.output}")
        print(f"Found {len(significant_results)} significantly enriched GO terms")
        
        # Print top results
        if significant_results:
            print("\nTop enriched GO terms:")
            for i, result in enumerate(significant_results[:5], 1):
                print(f"{i}. {result['go_name']} ({result['go_id']})")
                print(f"   Genes: {result['input_gene_count']}, Enrichment: {result['enrichment_ratio']:.2f}, p-adj: {result['corrected_p_value']:.2e}")
                
    except IOError as e:
        print(f"Error writing output file: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
