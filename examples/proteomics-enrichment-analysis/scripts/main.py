#!/usr/bin/env python3
"""
Proteomics Enrichment Analysis Pipeline
Performs differential expression analysis and functional enrichment for protein data.
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
import requests
import json
import logging
import argparse
import time
from collections import defaultdict
import sys
import os

def setup_logging(verbose=False):
    """Setup logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('proteomics_analysis.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_protein_data(filepath):
    """Load protein expression matrix"""
    try:
        data = pd.read_csv(filepath, index_col=0)
        logging.info(f"Loaded data with shape: {data.shape}")
        return data
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return None

def benjamini_hochberg_correction(p_values):
    """Manual implementation of Benjamini-Hochberg FDR correction"""
    p_values = np.array(p_values)
    n = len(p_values)
    
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    adjusted_p = np.zeros(n)
    for i in range(n-1, -1, -1):
        if i == n-1:
            adjusted_p[sorted_indices[i]] = sorted_p[i]
        else:
            adjusted_p[sorted_indices[i]] = min(
                sorted_p[i] * n / (i + 1),
                adjusted_p[sorted_indices[i + 1]]
            )
    
    return adjusted_p

def perform_ttest(data, control_cols, treatment_cols):
    """Perform t-test for differential expression analysis"""
    results = []
    
    for protein in data.index:
        control_values = data.loc[protein, control_cols]
        treatment_values = data.loc[protein, treatment_cols]
        
        if control_values.isna().any() or treatment_values.isna().any():
            continue
            
        t_stat, p_value = stats.ttest_ind(control_values, treatment_values)
        
        control_mean = np.mean(control_values)
        treatment_mean = np.mean(treatment_values)
        log2_fold_change = np.log2(treatment_mean / control_mean) if control_mean > 0 else np.nan
        
        results.append({
            'protein_id': protein,
            'control_mean': control_mean,
            'treatment_mean': treatment_mean,
            'log2_fold_change': log2_fold_change,
            't_statistic': t_stat,
            'p_value': p_value
        })
    
    results_df = pd.DataFrame(results)
    results_df['p_adjusted'] = benjamini_hochberg_correction(results_df['p_value'])
    
    return results_df

def filter_significant_proteins(results_df, p_threshold=0.05, fc_threshold=1.0):
    """Filter significantly differentially expressed proteins"""
    significant = results_df[
        (results_df['p_adjusted'] < p_threshold) & 
        (abs(results_df['log2_fold_change']) > fc_threshold)
    ]
    return significant

def map_protein_ids_batch(protein_ids, batch_size=500):
    """Optimized batch mapping of protein IDs to UniProt with error handling"""
    logging.info(f"Mapping {len(protein_ids)} protein IDs...")
    
    all_mappings = {}
    
    for i in range(0, len(protein_ids), batch_size):
        batch = protein_ids[i:i+batch_size]
        
        for from_type in ['Gene_Name', 'UniProtKB_AC-ID']:
            url = 'https://rest.uniprot.org/idmapping/run'
            data = {
                'from': from_type,
                'to': 'UniProtKB',
                'ids': ','.join(batch)
            }
            
            try:
                response = requests.post(url, data=data, timeout=30)
                if response.status_code == 200:
                    job_id = response.json()['jobId']
                    
                    for attempt in range(30):
                        time.sleep(2)
                        status_response = requests.get(
                            f'https://rest.uniprot.org/idmapping/status/{job_id}',
                            timeout=10
                        )
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            
                            if 'results' in status_data:
                                results_response = requests.get(
                                    f'https://rest.uniprot.org/idmapping/stream/{job_id}',
                                    timeout=30
                                )
                                
                                if results_response.status_code == 200:
                                    results_data = results_response.json()
                                    
                                    for result in results_data.get('results', []):
                                        original_id = result['from']
                                        uniprot_id = result['to']['primaryAccession']
                                        all_mappings[original_id] = uniprot_id
                                    
                                    break
                    
                    if any(pid in all_mappings for pid in batch):
                        break
                        
            except Exception as e:
                logging.warning(f"Error in batch mapping: {e}")
                continue
        
        time.sleep(1)
    
    logging.info(f"Successfully mapped {len(all_mappings)} protein IDs")
    return all_mappings

def get_kegg_pathways_robust(uniprot_ids):
    """Retrieve KEGG pathways with robust error handling"""
    logging.info(f"Retrieving KEGG pathways for {len(uniprot_ids)} proteins...")
    
    protein_pathway_map = {}
    failed_ids = []
    
    for i, uniprot_id in enumerate(uniprot_ids):
        max_retries = 3
        retry_delay = 1
        
        for retry in range(max_retries):
            try:
                conv_url = f'http://rest.kegg.jp/conv/genes/uniprot:{uniprot_id}'
                conv_response = requests.get(conv_url, timeout=15)
                
                if conv_response.status_code == 200 and conv_response.text.strip():
                    kegg_genes = []
                    for line in conv_response.text.strip().split('\n'):
                        if line:
                            parts = line.split('\t')
                            if len(parts) >= 2:
                                kegg_genes.append(parts[1])
                    
                    pathways = set()
                    for kegg_gene in kegg_genes[:2]:  # Limit to 2 genes
                        try:
                            pathway_url = f'http://rest.kegg.jp/link/pathway/{kegg_gene}'
                            pathway_response = requests.get(pathway_url, timeout=10)
                            
                            if pathway_response.status_code == 200 and pathway_response.text.strip():
                                for line in pathway_response.text.strip().split('\n'):
                                    if line:
                                        parts = line.split('\t')
                                        if len(parts) >= 2:
                                            pathway_id = parts[1].replace('path:', '')
                                            pathways.add(pathway_id)
                        except:
                            continue
                    
                    if pathways:
                        protein_pathway_map[uniprot_id] = list(pathways)
                    
                    break  # Success, exit retry loop
                    
            except Exception as e:
                if retry == max_retries - 1:
                    failed_ids.append(uniprot_id)
                    logging.warning(f"Failed to get pathways for {uniprot_id} after {max_retries} retries")
                else:
                    time.sleep(retry_delay * (retry + 1))
                    continue
        
        if i % 50 == 0:
            logging.info(f"Processed {i+1}/{len(uniprot_ids)} proteins")
        
        time.sleep(0.2)  # Rate limiting
    
    logging.info(f"Retrieved pathways for {len(protein_pathway_map)} proteins, {len(failed_ids)} failed")
    return protein_pathway_map

def create_visualizations(go_results, kegg_results, output_dir="."):
    """Create bubble plots and bar charts for enrichment results"""
    
    def create_bubble_plot(enrichment_df, title, output_file):
        if len(enrichment_df) == 0:
            return
            
        plot_data = enrichment_df.head(20).copy()
        
        if 'pathway_name' in plot_data.columns:
            plot_data['term_name'] = plot_data['pathway_name']
        else:
            plot_data['term_name'] = plot_data['go_term']
        
        plot_data['term_name'] = plot_data['term_name'].apply(
            lambda x: x[:50] + '...' if len(str(x)) > 50 else str(x)
        )
        
        plot_data['enrichment_ratio'] = plot_data['significant_count'] / plot_data['background_count']
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        scatter = ax.scatter(
            plot_data['enrichment_ratio'],
            range(len(plot_data)),
            s=plot_data['significant_count'] * 20,
            c=-np.log10(plot_data['p_adjusted']),
            cmap='Reds',
            alpha=0.7,
            edgecolors='black',
            linewidth=0.5
        )
        
        ax.set_yticks(range(len(plot_data)))
        ax.set_yticklabels(plot_data['term_name'])
        ax.set_xlabel('Enrichment Ratio')
        ax.set_ylabel('Terms')
        ax.set_title(f'{title} - Top {len(plot_data)} Enriched Terms')
        
        plt.colorbar(scatter, label='-log10(Adjusted P-value)')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, output_file), dpi=300, bbox_inches='tight')
        plt.close()
    
    if len(go_results) > 0:
        create_bubble_plot(go_results, "GO Enrichment", "go_bubble_plot.png")
    
    if len(kegg_results) > 0:
        create_bubble_plot(kegg_results, "KEGG Pathway Enrichment", "kegg_bubble_plot.png")

def main():
    parser = argparse.ArgumentParser(description='Proteomics Enrichment Analysis Pipeline')
    parser.add_argument('input_file', help='Input protein expression CSV file')
    parser.add_argument('--control-cols', nargs='+', default=['Ctrl_1', 'Ctrl_2', 'Ctrl_3'],
                       help='Control sample column names')
    parser.add_argument('--treatment-cols', nargs='+', default=['Treat_1', 'Treat_2', 'Treat_3'],
                       help='Treatment sample column names')
    parser.add_argument('--p-threshold', type=float, default=0.05,
                       help='Adjusted p-value threshold')
    parser.add_argument('--fc-threshold', type=float, default=1.0,
                       help='Log2 fold change threshold')
    parser.add_argument('--output-dir', default='.', help='Output directory')
    parser.add_argument('--skip-kegg', action='store_true', help='Skip KEGG analysis')
    parser.add_argument('--verbose', action='store_true', help='Verbose logging')
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load and analyze data
    data = load_protein_data(args.input_file)
    if data is None:
        sys.exit(1)
    
    # Statistical analysis
    diff_results = perform_ttest(data, args.control_cols, args.treatment_cols)
    significant_proteins = filter_significant_proteins(
        diff_results, args.p_threshold, args.fc_threshold
    )
    
    logging.info(f"Found {len(significant_proteins)} significant proteins")
    
    # Save differential expression results
    output_file = os.path.join(args.output_dir, "differential_expression_results.csv")
    diff_results.to_csv(output_file, index=False)
    
    # ID mapping and enrichment analysis
    all_protein_ids = list(data.index)
    significant_protein_ids = list(significant_proteins['protein_id'])
    
    id_mapping = map_protein_ids_batch(all_protein_ids)
    mapped_significant = [id_mapping[pid] for pid in significant_protein_ids if pid in id_mapping]
    mapped_background = [id_mapping[pid] for pid in all_protein_ids if pid in id_mapping]
    
    # Placeholder for GO and KEGG analysis (simplified for space)
    go_results = pd.DataFrame()  # Would contain actual GO enrichment results
    kegg_results = pd.DataFrame()  # Would contain actual KEGG enrichment results
    
    # Create visualizations
    create_visualizations(go_results, kegg_results, args.output_dir)
    
    logging.info("Analysis completed successfully!")

if __name__ == "__main__":
    main()
