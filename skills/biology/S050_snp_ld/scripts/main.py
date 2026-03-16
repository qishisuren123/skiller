#!/usr/bin/env python3
import argparse
import numpy as np
import pandas as pd
import logging
from itertools import combinations
import os
import sys
from scipy import stats
import math

def setup_logging():
    """Set up logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def parse_snp_position(snp_header):
    """Extract chromosome and position from SNP header (format: chr:position)"""
    try:
        chr_pos = snp_header.split(':')
        if len(chr_pos) != 2:
            raise ValueError(f"Invalid SNP header format: {snp_header}")
        chromosome = chr_pos[0]
        position = int(chr_pos[1])
        return chromosome, position
    except (ValueError, IndexError) as e:
        logging.error(f"Error parsing SNP position {snp_header}: {e}")
        return None, None

def load_genotype_data(filepath):
    """Load genotype data from tab-separated file"""
    logging.info(f"Loading genotype data from {filepath}")
    try:
        df = pd.read_csv(filepath, sep='\t', index_col=0)
        logging.info(f"Loaded data: {df.shape[0]} individuals, {df.shape[1]} SNPs")
        return df
    except Exception as e:
        logging.error(f"Error loading genotype data: {e}")
        sys.exit(1)

def calculate_haplotype_frequencies(geno1, geno2):
    """Calculate haplotype frequencies using EM algorithm"""
    # Count genotype combinations
    counts = {}
    total = 0
    
    for g1, g2 in zip(geno1, geno2):
        if g1 != -1 and g2 != -1:  # Skip missing data
            key = (g1, g2)
            counts[key] = counts.get(key, 0) + 1
            total += 1
    
    if total == 0:
        return None
    
    # Initialize haplotype frequencies
    p00 = p01 = p10 = p11 = 0.25
    
    # EM algorithm iterations
    for _ in range(100):  # Max iterations
        old_p00 = p00
        
        # E-step: calculate expected counts
        exp_counts = {'00': 0, '01': 0, '10': 0, '11': 0}
        
        for (g1, g2), count in counts.items():
            if g1 == 0 and g2 == 0:  # 00/00
                exp_counts['00'] += 2 * count
            elif g1 == 0 and g2 == 1:  # 00/01
                exp_counts['00'] += count
                exp_counts['01'] += count
            elif g1 == 0 and g2 == 2:  # 00/11
                exp_counts['01'] += 2 * count
            elif g1 == 1 and g2 == 0:  # 01/00
                exp_counts['00'] += count
                exp_counts['10'] += count
            elif g1 == 1 and g2 == 1:  # 01/01 - phase ambiguous
                # Use current frequencies to resolve phase
                freq_cis = p00 * p11
                freq_trans = p01 * p10
                total_freq = freq_cis + freq_trans
                if total_freq > 0:
                    prob_cis = freq_cis / total_freq
                    exp_counts['00'] += count * prob_cis
                    exp_counts['11'] += count * prob_cis
                    exp_counts['01'] += count * (1 - prob_cis)
                    exp_counts['10'] += count * (1 - prob_cis)
                else:
                    exp_counts['00'] += count * 0.5
                    exp_counts['11'] += count * 0.5
                    exp_counts['01'] += count * 0.5
                    exp_counts['10'] += count * 0.5
            elif g1 == 1 and g2 == 2:  # 01/11
                exp_counts['01'] += count
                exp_counts['11'] += count
            elif g1 == 2 and g2 == 0:  # 11/00
                exp_counts['10'] += 2 * count
            elif g1 == 2 and g2 == 1:  # 11/01
                exp_counts['10'] += count
                exp_counts['11'] += count
            elif g1 == 2 and g2 == 2:  # 11/11
                exp_counts['11'] += 2 * count
        
        # M-step: update frequencies
        total_haps = sum(exp_counts.values())
        if total_haps > 0:
            p00 = exp_counts['00'] / total_haps
            p01 = exp_counts['01'] / total_haps
            p10 = exp_counts['10'] / total_haps
            p11 = exp_counts['11'] / total_haps
        
        # Check convergence
        if abs(p00 - old_p00) < 1e-6:
            break
    
    return {'p00': p00, 'p01': p01, 'p10': p10, 'p11': p11}

def calculate_ld_stats(geno1, geno2):
    """Calculate LD statistics (D', r², LOD) for two SNPs"""
    # Remove missing data
    valid_mask = (geno1 != -1) & (geno2 != -1)
    g1 = geno1[valid_mask]
    g2 = geno2[valid_mask]
    
    if len(g1) < 10:  # Minimum sample size
        return None
    
    # Calculate allele frequencies
    p1 = np.mean(g1) / 2.0  # Frequency of allele 1 at SNP1
    p2 = np.mean(g2) / 2.0  # Frequency of allele 1 at SNP2
    
    if p1 == 0 or p1 == 1 or p2 == 0 or p2 == 1:
        return None  # Monomorphic
    
    # Calculate haplotype frequencies
    hap_freqs = calculate_haplotype_frequencies(g1, g2)
    if hap_freqs is None:
        return None
    
    # Calculate D
    D = hap_freqs['p11'] - p1 * p2
    
    # Calculate D'
    if D >= 0:
        D_max = min(p1 * (1 - p2), (1 - p1) * p2)
    else:
        D_max = max(-p1 * p2, -(1 - p1) * (1 - p2))
    
    D_prime = D / D_max if D_max != 0 else 0
    
    # Calculate r²
    r_squared = (D ** 2) / (p1 * (1 - p1) * p2 * (1 - p2)) if p1 * (1 - p1) * p2 * (1 - p2) != 0 else 0
    
    # Calculate LOD score (simplified)
    # This is a basic implementation - more sophisticated methods exist
    correlation = np.corrcoef(g1, g2)[0, 1] if len(g1) > 1 else 0
    if not np.isnan(correlation) and correlation != 0:
        z_score = correlation * np.sqrt(len(g1) - 2) / np.sqrt(1 - correlation**2)
        lod_score = abs(z_score) / 4.605  # Convert to LOD (log10)
    else:
        lod_score = 0
    
    return {
        'D': D,
        'D_prime': D_prime,
        'r_squared': r_squared,
        'lod_score': lod_score,
        'sample_size': len(g1),
        'haplotype_freqs': hap_freqs
    }

def main():
    parser = argparse.ArgumentParser(description='SNP Linkage Disequilibrium Analysis')
    parser.add_argument('input_file', help='Input genotype file (tab-separated)')
    parser.add_argument('output_dir', help='Output directory')
    parser.add_argument('--max_distance', type=int, default=100000, 
                       help='Maximum distance between SNPs (bp)')
    parser.add_argument('--r2_threshold', type=float, default=0.8,
                       help='r² threshold for significance')
    parser.add_argument('--dprime_threshold', type=float, default=0.8,
                       help='|D\'| threshold for significance')
    parser.add_argument('--lod_threshold', type=float, default=3.0,
                       help='LOD score threshold for significance')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load data
    genotype_df = load_genotype_data(args.input_file)
    
    # Parse SNP positions
    snp_positions = {}
    for snp in genotype_df.columns:
        chr_name, pos = parse_snp_position(snp)
        if chr_name is not None and pos is not None:
            snp_positions[snp] = (chr_name, pos)
    
    logging.info(f"Successfully parsed {len(snp_positions)} SNP positions")
    
    # Calculate LD for SNP pairs
    results = []
    significant_pairs = []
    
    snp_list = list(snp_positions.keys())
    total_pairs = 0
    processed_pairs = 0
    
    for i, snp1 in enumerate(snp_list):
        for j, snp2 in enumerate(snp_list[i+1:], i+1):
            chr1, pos1 = snp_positions[snp1]
            chr2, pos2 = snp_positions[snp2]
            
            # Only analyze SNPs on same chromosome within distance threshold
            if chr1 == chr2 and abs(pos2 - pos1) <= args.max_distance:
                total_pairs += 1
                
                geno1 = genotype_df[snp1].values
                geno2 = genotype_df[snp2].values
                
                ld_stats = calculate_ld_stats(geno1, geno2)
                
                if ld_stats is not None:
                    result = {
                        'SNP1': snp1,
                        'SNP2': snp2,
                        'chr': chr1,
                        'pos1': pos1,
                        'pos2': pos2,
                        'distance': abs(pos2 - pos1),
                        **ld_stats
                    }
                    results.append(result)
                    
                    # Check significance
                    if (ld_stats['r_squared'] >= args.r2_threshold and
                        abs(ld_stats['D_prime']) >= args.dprime_threshold and
                        ld_stats['lod_score'] >= args.lod_threshold):
                        significant_pairs.append(result)
                    
                    processed_pairs += 1
                    
                    if processed_pairs % 1000 == 0:
                        logging.info(f"Processed {processed_pairs}/{total_pairs} SNP pairs")
    
    logging.info(f"Analysis complete. Found {len(significant_pairs)} significant pairs out of {len(results)} total pairs")
    
    # Write results
    if results:
        results_df = pd.DataFrame(results)
        results_file = os.path.join(args.output_dir, 'ld_results.txt')
        results_df.to_csv(results_file, sep='\t', index=False)
        logging.info(f"All results written to {results_file}")
    
    if significant_pairs:
        sig_df = pd.DataFrame(significant_pairs)
        sig_file = os.path.join(args.output_dir, 'significant_ld_pairs.txt')
        sig_df.to_csv(sig_file, sep='\t', index=False)
        logging.info(f"Significant pairs written to {sig_file}")

if __name__ == '__main__':
    main()
