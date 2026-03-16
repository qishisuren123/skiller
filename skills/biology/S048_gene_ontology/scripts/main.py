#!/usr/bin/env python3
import argparse
import json
import random
import logging
import math
import os
from collections import defaultdict
import numpy as np

def log_factorial(n):
    """Calculate log factorial to avoid overflow"""
    if n <= 1:
        return 0.0
    return sum(math.log(i) for i in range(2, n + 1))

def fisher_exact_test(a, b, c, d):
    """Manual implementation of Fisher's exact test"""
    n = a + b + c + d
    
    def table_prob(a, b, c, d):
        try:
            log_prob = (log_factorial(a + b) + log_factorial(c + d) + 
                       log_factorial(a + c) + log_factorial(b + d) - 
                       log_factorial(a) - log_factorial(b) - 
                       log_factorial(c) - log_factorial(d) - log_factorial(n))
            return math.exp(log_prob)
        except (OverflowError, ValueError):
            return 0.0
    
    current_prob = table_prob(a, b, c, d)
    p_value = 0.0
    min_cell = min(a + b, a + c)
    
    for i in range(a, min_cell + 1):
        new_b = (a + b) - i
        new_c = (a + c) - i  
        new_d = d + (a - i)
        
        if new_b >= 0 and new_c >= 0 and new_d >= 0:
            prob = table_prob(i, new_b, new_c, new_d)
            if prob <= current_prob * 1.000001:
                p_value += prob
    
    return min(1.0, p_value)

def chi_square_test(a, b, c, d):
    """Chi-square test with Yates' continuity correction"""
    n = a + b + c + d
    if n == 0:
        return 1.0
    
    expected_a = (a + b) * (a + c) / n
    expected_b = (a + b) * (b + d) / n
    expected_c = (c + d) * (a + c) / n
    expected_d = (c + d) * (b + d) / n
    
    if min(expected_a, expected_b, expected_c, expected_d) < 5:
        return fisher_exact_test(a, b, c, d)
    
    chi_square = (abs(a * d - b * c) - n / 2) ** 2 * n / ((a + b) * (c + d) * (a + c) * (b + d))
    p_value = math.exp(-chi_square / 2)
    
    return min(1.0, p_value)

def load_go_annotations(filepath):
    """Load gene-to-GO mappings from tab-separated file"""
    gene_to_go = defaultdict(list)
    go_terms = {}
    
    try:
        with open(filepath, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('\t')
                if len(parts) < 3:
                    logging.warning(f"Skipping malformed line {line_num}: {line}")
                    continue
                
                gene_id, go_term, description = parts[0], parts[1], parts[2]
                gene_to_go[gene_id].append(go_term)
                go_terms[go_term] = description
        
        logging.info(f"Loaded annotations for {len(gene_to_go)} genes with {len(go_terms)} GO terms")
        return gene_to_go, go_terms
        
    except FileNotFoundError:
        logging.error(f"GO annotation file not found: {filepath}")
        raise
    except Exception as e:
        logging.error(f"Error loading GO annotations: {e}")
        raise

def create_synthetic_go_database():
    """Create a synthetic gene-to-GO term mapping database"""
    go_terms = {
        'GO:0008150': 'biological_process',
        'GO:0003674': 'molecular_function', 
        'GO:0005575': 'cellular_component',
        'GO:0006412': 'translation',
        'GO:0006414': 'translational elongation',
        'GO:0006415': 'translational termination',
        'GO:0006413': 'translational initiation',
        'GO:0006281': 'DNA repair',
        'GO:0006260': 'DNA replication',
        'GO:0006351': 'transcription, DNA-templated',
        'GO:0006355': 'regulation of transcription, DNA-templated',
        'GO:0000278': 'mitotic cell cycle',
        'GO:0007049': 'cell cycle',
        'GO:0008283': 'cell proliferation',
        'GO:0006915': 'apoptotic process',
        'GO:0016310': 'phosphorylation',
        'GO:0006508': 'proteolysis',
        'GO:0055114': 'oxidation-reduction process',
        'GO:0006810': 'transport',
        'GO:0005886': 'plasma membrane'
    }
    
    random.seed(42)
    genes = [f"GENE_{i:04d}" for i in range(1, 1001)]
    
    gene_to_go = defaultdict(list)
    for gene in genes:
        num_terms = random.randint(1, 5)
        selected_terms = random.sample(list(go_terms.keys()), num_terms)
        gene_to_go[gene] = selected_terms
    
    return gene_to_go, go_terms

def parse_gene_list(gene_string):
    """Parse comma or space separated gene list"""
    if ',' in gene_string:
        return [gene.strip() for gene in gene_string.split(',')]
    else:
        return gene_string.split()

def calculate_enrichment(input_genes, background_genes, gene_to_go, go_terms, use_fast_test=True):
    """Calculate GO term enrichment statistics"""
    results = []
    
    input_go_counts = defaultdict(int)
    background_go_counts = defaultdict(int)
    
    for gene in input_genes:
        if gene in gene_to_go:
            for go_term in gene_to_go[gene]:
                input_go_counts[go_term] += 1
    
    for gene in background_genes:
        if gene in gene_to_go:
            for go_term in gene_to_go[gene]:
                background_go_counts[go_term] += 1
    
    for go_term in input_go_counts:
        if input_go_counts[go_term] >= 2:
            a = input_go_counts[go_term]
            b = len(input_genes) - a
            
            background_only_genes = [g for g in background_genes if g not in input_genes]
            background_only_with_term = sum(1 for gene in background_only_genes 
                                          if gene in gene_to_go and go_term in gene_to_go[gene])
            
            c = background_only_with_term
            d = len(background_only_genes) - c
            
            if a < 0 or b < 0 or c < 0 or d < 0:
                continue
            
            if use_fast_test:
                p_value = chi_square_test(a, b, c, d)
            else:
                p_value = fisher_exact_test(a, b, c, d)
            
            observed_freq = a / len(input_genes)
            total_background_with_term = background_go_counts[go_term]
            expected_freq = total_background_with_term / len(background_genes)
            
            enrichment_ratio = observed_freq / expected_freq if expected_freq > 0 else float('inf')
            
            results.append({
                'go_term': go_term,
                'description': go_terms.get(go_term, 'Unknown'),
                'input_count': a,
                'background_count': total_background_with_term,
                'enrichment_ratio': enrichment_ratio,
                'p_value': p_value
            })
    
    return results

def main():
    logging.basicConfig(level=logging.INFO)
    
    parser = argparse.ArgumentParser(description='Gene Ontology Enrichment Analysis')
    parser.add_argument('--genes', required=True, help='Input gene list (comma or space separated)')
    parser.add_argument('--background', help='Background gene set (comma or space separated)')
    parser.add_argument('--annotations', help='GO annotations file (tab-separated: gene_id\\tgo_term\\tdescription)')
    parser.add_argument('--output', default='go_enrichment.json', help='Output JSON file')
    parser.add_argument('--fast', action='store_true', help='Use chi-square approximation for faster computation')
    
    args = parser.parse_args()
    
    if args.annotations and os.path.exists(args.annotations):
        gene_to_go, go_terms = load_go_annotations(args.annotations)
    else:
        if args.annotations:
            logging.warning(f"Annotations file {args.annotations} not found, using synthetic data")
        gene_to_go, go_terms = create_synthetic_go_database()
    
    input_genes = parse_gene_list(args.genes)
    logging.info(f"Analyzing {len(input_genes)} input genes")
    
    if args.background:
        background_genes = parse_gene_list(args.background)
    else:
        background_genes = list(gene_to_go.keys())
    
    logging.info(f"Using {len(background_genes)} background genes")
    
    results = calculate_enrichment(input_genes, background_genes, gene_to_go, go_terms, args.fast)
    
    if results:
        num_tests = len(results)
        for result in results:
            result['corrected_p_value'] = min(1.0, result['p_value'] * num_tests)
        
        significant_results = [r for r in results if r['corrected_p_value'] < 0.05]
        significant_results.sort(key=lambda x: x['corrected_p_value'])
        
        with open(args.output, 'w') as f:
            json.dump(significant_results, f, indent=2)
        
        print(f"Found {len(significant_results)} significantly enriched GO terms")
        print(f"Results saved to {args.output}")
        
        if significant_results:
            print("\nTop enriched terms:")
            for i, result in enumerate(significant_results[:5]):
                print(f"{i+1}. {result['go_term']}: {result['description']}")
                print(f"   Input: {result['input_count']}, Background: {result['background_count']}")
                print(f"   Enrichment: {result['enrichment_ratio']:.2f}, p-value: {result['corrected_p_value']:.2e}")
    else:
        print("No GO terms found with at least 2 genes")

if __name__ == "__main__":
    main()
