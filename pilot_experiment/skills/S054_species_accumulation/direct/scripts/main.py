#!/usr/bin/env python3
"""
Species Accumulation Curve Analysis
Computes and analyzes species accumulation curves from ecological sampling data.
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import argparse
import os
from pathlib import Path
from scipy.special import comb

def generate_synthetic_data(n_sites, n_species_pool, seed=42):
    """Generate synthetic ecological sampling data with realistic species distributions."""
    np.random.seed(seed)
    
    # Generate species abundance distribution (log-normal)
    species_abundances = np.random.lognormal(mean=2, sigma=1.5, size=n_species_pool)
    species_abundances = species_abundances / np.sum(species_abundances)
    
    # Create site-by-species occurrence matrix
    occurrence_matrix = np.zeros((n_sites, n_species_pool), dtype=int)
    
    for site in range(n_sites):
        # Number of species at this site (varies by site)
        n_species_site = np.random.poisson(lam=15) + 5  # 5-35 species per site typically
        n_species_site = min(n_species_site, n_species_pool)
        
        # Select species based on abundance weights
        selected_species = np.random.choice(
            n_species_pool, 
            size=n_species_site, 
            replace=False, 
            p=species_abundances
        )
        occurrence_matrix[site, selected_species] = 1
    
    return occurrence_matrix

def compute_accumulation_curve(occurrence_matrix, n_randomizations=100):
    """Compute species accumulation curve with confidence intervals."""
    n_sites = occurrence_matrix.shape[0]
    accumulation_curves = []
    
    for _ in range(n_randomizations):
        # Random site ordering
        site_order = np.random.permutation(n_sites)
        cumulative_species = []
        observed_species = set()
        
        for i in range(n_sites):
            site_idx = site_order[i]
            # Add species from this site
            site_species = set(np.where(occurrence_matrix[site_idx, :] == 1)[0])
            observed_species.update(site_species)
            cumulative_species.append(len(observed_species))
        
        accumulation_curves.append(cumulative_species)
    
    accumulation_curves = np.array(accumulation_curves)
    
    # Calculate statistics
    mean_curve = np.mean(accumulation_curves, axis=0)
    std_curve = np.std(accumulation_curves, axis=0)
    ci_lower = np.percentile(accumulation_curves, 2.5, axis=0)
    ci_upper = np.percentile(accumulation_curves, 97.5, axis=0)
    
    return {
        'mean': mean_curve,
        'std': std_curve,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'sites': np.arange(1, n_sites + 1)
    }

def sample_based_rarefaction(occurrence_matrix, max_sites=None):
    """Calculate sample-based rarefaction curve."""
    n_sites, n_species = occurrence_matrix.shape
    if max_sites is None:
        max_sites = n_sites
    
    rarefied_richness = []
    
    for m in range(1, min(max_sites + 1, n_sites + 1)):
        expected_species = 0
        
        for j in range(n_species):
            # Number of sites where species j occurs
            sites_with_species = np.sum(occurrence_matrix[:, j])
            
            if sites_with_species > 0:
                # Probability that species j is NOT in a random sample of m sites
                if sites_with_species >= m:
                    prob_absent = 0  # Species definitely present
                else:
                    # Hypergeometric probability
                    sites_without_species = n_sites - sites_with_species
                    if sites_without_species >= m:
                        prob_absent = 1.0
                    else:
                        prob_absent = comb(sites_without_species, m, exact=True) / comb(n_sites, m, exact=True)
                
                expected_species += (1 - prob_absent)
        
        rarefied_richness.append(expected_species)
    
    return np.array(rarefied_richness)

def calculate_chao2_estimator(occurrence_matrix):
    """Calculate Chao2 estimator for asymptotic species richness."""
    n_sites = occurrence_matrix.shape[0]
    
    # Calculate incidence frequencies
    species_incidences = np.sum(occurrence_matrix, axis=0)
    
    # Count species by incidence frequency
    Q1 = np.sum(species_incidences == 1)  # Species in exactly 1 site
    Q2 = np.sum(species_incidences == 2)  # Species in exactly 2 sites
    S_obs = np.sum(species_incidences > 0)  # Observed species richness
    
    # Chao2 estimator
    if Q2 > 0:
        chao2 = S_obs + (Q1 * Q1) / (2 * Q2)
    else:
        # Fallback when Q2 = 0
        chao2 = S_obs + (Q1 * (Q1 - 1)) / 2
    
    return chao2, S_obs, Q1, Q2

def create_visualization(accumulation_data, rarefaction_data, chao2_estimate, output_path):
    """Create species accumulation curve visualization."""
    plt.figure(figsize=(12, 8))
    
    sites = accumulation_data['sites']
    rarefaction_sites = np.arange(1, len(rarefaction_data) + 1)
    
    # Plot observed accumulation curve with confidence intervals
    plt.fill_between(sites, accumulation_data['ci_lower'], accumulation_data['ci_upper'], 
                     alpha=0.3, color='blue', label='95% CI (observed)')
    plt.plot(sites, accumulation_data['mean'], 'b-', linewidth=2, label='Observed accumulation')
    
    # Plot rarefaction curve
    plt.plot(rarefaction_sites, rarefaction_data, 'r--', linewidth=2, label='Sample-based rarefaction')
    
    # Plot asymptotic estimate
    plt.axhline(y=chao2_estimate, color='green', linestyle=':', linewidth=2, 
                label=f'Chao2 estimate ({chao2_estimate:.1f})')
    
    plt.xlabel('Number of Sites', fontsize=12)
    plt.ylabel('Cumulative Species Richness', fontsize=12)
    plt.title('Species Accumulation Curve Analysis', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Species Accumulation Curve Analysis')
    parser.add_argument('--sites', type=int, default=50, help='Number of sampling sites')
    parser.add_argument('--species-pool', type=int, default=100, help='Total species pool size')
    parser.add_argument('--randomizations', type=int, default=100, help='Number of randomizations')
    parser.add_argument('--output-dir', type=str, default='output', help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed for reproducibility')
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print(f"Generating synthetic data: {args.sites} sites, {args.species_pool} species pool")
    
    # Generate synthetic data
    occurrence_matrix = generate_synthetic_data(args.sites, args.species_pool, args.seed)
    
    print("Computing species accumulation curves...")
    
    # Compute accumulation curve
    accumulation_data = compute_accumulation_curve(occurrence_matrix, args.randomizations)
    
    # Compute rarefaction curve
    rarefaction_data = sample_based_rarefaction(occurrence_matrix)
    
    # Calculate Chao2 estimator
    chao2_estimate, s_obs, q1, q2 = calculate_chao2_estimator(occurrence_matrix)
    
    # Calculate summary statistics
    mean_species_per_site = np.mean(np.sum(occurrence_matrix, axis=1))
    total_observed_species = s_obs
    
    summary_stats = {
        'total_sites': args.sites,
        'species_pool_size': args.species_pool,
        'observed_species_richness': int(total_observed_species),
        'mean_species_per_site': float(mean_species_per_site),
        'chao2_estimate': float(chao2_estimate),
        'singletons_q1': int(q1),
        'doubletons_q2': int(q2),
        'sampling_completeness': float(total_observed_species / chao2_estimate * 100)
    }
    
    print(f"\nResults Summary:")
    print(f"Observed species richness: {summary_stats['observed_species_richness']}")
    print(f"Mean species per site: {summary_stats['mean_species_per_site']:.1f}")
    print(f"Chao2 estimate: {summary_stats['chao2_estimate']:.1f}")
    print(f"Sampling completeness: {summary_stats['sampling_completeness']:.1f}%")
    
    # Create visualization
    print("Creating visualization...")
    plot_path = output_dir / 'species_accumulation_curve.png'
    create_visualization(accumulation_data, rarefaction_data, chao2_estimate, plot_path)
    
    # Export results to JSON
    results = {
        'summary_statistics': summary_stats,
        'accumulation_curve': {
            'sites': accumulation_data['sites'].tolist(),
            'mean_richness': accumulation_data['mean'].tolist(),
            'ci_lower': accumulation_data['ci_lower'].tolist(),
            'ci_upper': accumulation_data['ci_upper'].tolist()
        },
        'rarefaction_curve': {
            'sites': list(range(1, len(rarefaction_data) + 1)),
            'expected_richness': rarefaction_data.tolist()
        }
    }
    
    json_path = output_dir / 'accumulation_analysis.json'
    with open(json_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Export occurrence matrix to CSV
    species_names = [f'Species_{i+1:03d}' for i in range(args.species_pool)]
    site_names = [f'Site_{i+1:03d}' for i in range(args.sites)]
    
    occurrence_df = pd.DataFrame(occurrence_matrix, 
                                index=site_names, 
                                columns=species_names)
    
    csv_path = output_dir / 'site_species_matrix.csv'
    occurrence_df.to_csv(csv_path)
    
    print(f"\nOutput files saved to {output_dir}:")
    print(f"- {plot_path.name}: Species accumulation curve plot")
    print(f"- {json_path.name}: Analysis results and statistics")
    print(f"- {csv_path.name}: Site-by-species occurrence matrix")

if __name__ == '__main__':
    main()
