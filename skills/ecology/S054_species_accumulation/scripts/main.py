#!/usr/bin/env python3
"""
Species Accumulation Curve Analysis Tool
Generates synthetic ecological data and computes species accumulation curves
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
import logging
from pathlib import Path
from scipy import stats
from scipy.special import comb
from collections import defaultdict
import random

def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def generate_synthetic_data(n_sites, n_species_pool, seed=42):
    """
    Generate synthetic species occurrence data with realistic patterns
    
    Args:
        n_sites: Number of sampling sites
        n_species_pool: Total species pool size
        seed: Random seed for reproducibility
    
    Returns:
        pandas.DataFrame: Site-by-species occurrence matrix
    """
    np.random.seed(seed)
    random.seed(seed)
    
    # Create species names
    species_names = [f"Species_{i:03d}" for i in range(n_species_pool)]
    site_names = [f"Site_{i:03d}" for i in range(n_sites)]
    
    # Initialize occurrence matrix
    occurrence_matrix = np.zeros((n_sites, n_species_pool), dtype=int)
    
    # Generate species occurrence probabilities (some species are rarer)
    species_probs = np.random.lognormal(mean=-1.5, sigma=1.0, size=n_species_pool)
    species_probs = species_probs / np.max(species_probs) * 0.3  # Scale to reasonable range
    
    # For each site, determine which species are present
    for site_idx in range(n_sites):
        # Each site has 5-25 species on average
        n_species_site = np.random.poisson(15)
        n_species_site = min(n_species_site, n_species_pool)
        
        # Select species based on their occurrence probabilities
        present_species = np.random.choice(
            n_species_pool, 
            size=n_species_site, 
            replace=False, 
            p=species_probs/np.sum(species_probs)
        )
        
        occurrence_matrix[site_idx, present_species] = 1
    
    # Convert to DataFrame
    df = pd.DataFrame(occurrence_matrix, 
                     index=site_names, 
                     columns=species_names)
    
    logging.info(f"Generated synthetic data: {n_sites} sites, {n_species_pool} species pool")
    return df

def compute_species_accumulation(occurrence_df, n_randomizations=100):
    """
    Compute species accumulation curve with confidence intervals
    
    Args:
        occurrence_df: Site-by-species occurrence matrix
        n_randomizations: Number of random site orderings
    
    Returns:
        dict: Accumulation curve data
    """
    n_sites = len(occurrence_df)
    accumulation_curves = np.zeros((n_randomizations, n_sites))
    
    for rand_iter in range(n_randomizations):
        # Randomly order sites
        site_order = np.random.permutation(n_sites)
        cumulative_species = set()
        
        for i, site_idx in enumerate(site_order):
            # Get species present at this site
            site_species = set(occurrence_df.columns[occurrence_df.iloc[site_idx] == 1])
            cumulative_species.update(site_species)
            accumulation_curves[rand_iter, i] = len(cumulative_species)
    
    # Calculate statistics
    mean_curve = np.mean(accumulation_curves, axis=0)
    ci_lower = np.percentile(accumulation_curves, 2.5, axis=0)
    ci_upper = np.percentile(accumulation_curves, 97.5, axis=0)
    
    return {
        'sites': np.arange(1, n_sites + 1),
        'mean': mean_curve,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'all_curves': accumulation_curves
    }

def compute_rarefaction(occurrence_df, max_sites=None):
    """
    Compute sample-based rarefaction curve with numerical stability
    
    Args:
        occurrence_df: Site-by-species occurrence matrix
        max_sites: Maximum number of sites for rarefaction (default: all sites)
    
    Returns:
        dict: Rarefaction curve data
    """
    n_sites = len(occurrence_df)
    if max_sites is None:
        max_sites = n_sites
    
    # Calculate species frequencies (number of sites where each species occurs)
    species_frequencies = occurrence_df.sum(axis=0)
    species_frequencies = species_frequencies[species_frequencies > 0]  # Remove absent species
    
    rarefaction_curve = []
    site_range = range(1, min(max_sites + 1, n_sites + 1))
    
    for m in site_range:
        # Expected number of species in m sites
        expected_species = 0
        
        for freq in species_frequencies:
            if freq > 0 and m <= n_sites:
                # Use scipy.special.comb with exact=False for floating point calculation
                # This avoids integer overflow issues
                try:
                    if n_sites - freq >= m:
                        # Probability that species is NOT in m randomly chosen sites
                        prob_absent = comb(n_sites - freq, m, exact=False) / comb(n_sites, m, exact=False)
                        # Probability that species IS in m randomly chosen sites
                        prob_present = 1 - prob_absent
                    else:
                        # If freq > n_sites - m, species must be present
                        prob_present = 1.0
                    
                    expected_species += prob_present
                    
                except (OverflowError, ValueError):
                    # Fallback for extreme cases - use hypergeometric approximation
                    prob_present = min(1.0, freq * m / n_sites)
                    expected_species += prob_present
        
        rarefaction_curve.append(expected_species)
    
    return {
        'sites': np.array(list(site_range)),
        'expected_species': np.array(rarefaction_curve)
    }

def calculate_chao2(occurrence_df):
    """
    Calculate Chao2 estimator for asymptotic species richness
    
    Args:
        occurrence_df: Site-by-species occurrence matrix
    
    Returns:
        dict: Chao2 estimate and components
    """
    n_sites = len(occurrence_df)
    
    # Calculate species frequencies
    species_frequencies = occurrence_df.sum(axis=0)
    species_frequencies = species_frequencies[species_frequencies > 0]  # Remove absent species
    
    # Count species occurring in exactly 1 or 2 sites
    Q1 = np.sum(species_frequencies == 1)  # Uniques
    Q2 = np.sum(species_frequencies == 2)  # Duplicates
    S_obs = len(species_frequencies)  # Observed species richness
    
    # Chao2 estimator
    if Q2 > 0:
        chao2 = S_obs + (Q1**2) / (2 * Q2)
    else:
        # Modified estimator when Q2 = 0
        chao2 = S_obs + Q1 * (Q1 - 1) / 2
    
    return {
        'chao2_estimate': chao2,
        'observed_richness': S_obs,
        'uniques': Q1,
        'duplicates': Q2,
        'completeness': S_obs / chao2 if chao2 > 0 else 1.0
    }

def calculate_summary_stats(occurrence_df, accumulation_data, chao2_data):
    """
    Calculate summary statistics for the analysis
    """
    species_per_site = occurrence_df.sum(axis=1)
    total_species = occurrence_df.sum(axis=0).astype(bool).sum()
    
    # Calculate accumulation rate (species gained per additional site)
    accumulation_rate = np.diff(accumulation_data['mean']).mean()
    
    return {
        'total_species_observed': int(total_species),
        'mean_species_per_site': float(species_per_site.mean()),
        'std_species_per_site': float(species_per_site.std()),
        'min_species_per_site': int(species_per_site.min()),
        'max_species_per_site': int(species_per_site.max()),
        'accumulation_rate': float(accumulation_rate),
        'chao2_estimate': float(chao2_data['chao2_estimate']),
        'sampling_completeness': float(chao2_data['completeness'])
    }

def create_visualization(accumulation_data, rarefaction_data, chao2_data, output_path):
    """
    Create species accumulation curve visualization
    
    Args:
        accumulation_data: Species accumulation curve data
        rarefaction_data: Rarefaction curve data
        chao2_data: Chao2 estimator data
        output_path: Path to save the plot
    """
    plt.figure(figsize=(12, 8))
    
    # Plot observed accumulation curve with confidence intervals
    plt.fill_between(accumulation_data['sites'], 
                    accumulation_data['ci_lower'], 
                    accumulation_data['ci_upper'], 
                    alpha=0.3, color='blue', label='95% CI')
    
    plt.plot(accumulation_data['sites'], accumulation_data['mean'], 
            'b-', linewidth=2, label='Observed accumulation')
    
    # Plot rarefaction curve
    plt.plot(rarefaction_data['sites'], rarefaction_data['expected_species'], 
            'g--', linewidth=2, label='Rarefaction curve')
    
    # Add horizontal line for Chao2 asymptotic estimate
    plt.axhline(y=chao2_data['chao2_estimate'], color='red', linestyle=':', 
               linewidth=2, label=f'Chao2 estimate ({chao2_data["chao2_estimate"]:.1f})')
    
    plt.xlabel('Number of Sites', fontsize=12)
    plt.ylabel('Cumulative Species Richness', fontsize=12)
    plt.title('Species Accumulation Curve Analysis', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    
    # Add text box with key statistics
    textstr = f'''Observed richness: {chao2_data["observed_richness"]}
Chao2 estimate: {chao2_data["chao2_estimate"]:.1f}
Completeness: {chao2_data["completeness"]:.1%}
Uniques: {chao2_data["uniques"]}
Duplicates: {chao2_data["duplicates"]}'''
    
    props = dict(boxstyle='round', facecolor='wheat', alpha=0.8)
    plt.text(0.02, 0.98, textstr, transform=plt.gca().transAxes, fontsize=9,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    logging.info(f"Visualization saved to {output_path}")

def export_results(accumulation_data, rarefaction_data, chao2_data, summary_stats, output_path):
    """
    Export analysis results to JSON file
    
    Args:
        accumulation_data: Species accumulation curve data
        rarefaction_data: Rarefaction curve data  
        chao2_data: Chao2 estimator data
        summary_stats: Summary statistics
        output_path: Path to save JSON file
    """
    results = {
        'summary_statistics': summary_stats,
        'chao2_analysis': chao2_data,
        'species_accumulation': {
            'sites': accumulation_data['sites'].tolist(),
            'mean_richness': accumulation_data['mean'].tolist(),
            'ci_lower': accumulation_data['ci_lower'].tolist(),
            'ci_upper': accumulation_data['ci_upper'].tolist()
        },
        'rarefaction_analysis': {
            'sites': rarefaction_data['sites'].tolist(),
            'expected_richness': rarefaction_data['expected_species'].tolist()
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logging.info(f"Results exported to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Species Accumulation Curve Analysis')
    parser.add_argument('--sites', type=int, default=50, help='Number of sampling sites')
    parser.add_argument('--species', type=int, default=100, help='Species pool size')
    parser.add_argument('--randomizations', type=int, default=100, help='Number of randomizations')
    parser.add_argument('--output', type=str, default='output', help='Output directory')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    
    args = parser.parse_args()
    
    setup_logging()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(exist_ok=True)
    
    # Generate synthetic data
    occurrence_data = generate_synthetic_data(args.sites, args.species, args.seed)
    
    # Compute species accumulation curve
    accumulation_data = compute_species_accumulation(occurrence_data, args.randomizations)
    
    # Compute rarefaction curve
    rarefaction_data = compute_rarefaction(occurrence_data)
    
    # Calculate Chao2 estimator
    chao2_data = calculate_chao2(occurrence_data)
    
    # Calculate summary statistics
    summary_stats = calculate_summary_stats(occurrence_data, accumulation_data, chao2_data)
    
    # Create visualization
    create_visualization(accumulation_data, rarefaction_data, chao2_data, 
                        output_dir / 'species_accumulation_plot.png')
    
    # Export results to JSON
    export_results(accumulation_data, rarefaction_data, chao2_data, summary_stats,
                  output_dir / 'analysis_results.json')
    
    # Save occurrence matrix to CSV
    occurrence_data.to_csv(output_dir / 'occurrence_matrix.csv')
    
    # Print results
    print("Species Accumulation Analysis Results:")
    print(f"Total species observed: {summary_stats['total_species_observed']}")
    print(f"Mean species per site: {summary_stats['mean_species_per_site']:.2f}")
    print(f"Chao2 asymptotic estimate: {summary_stats['chao2_estimate']:.2f}")
    print(f"Sampling completeness: {summary_stats['sampling_completeness']:.2%}")
    print(f"Results saved to: {output_dir}")
    
    logging.info("Analysis completed successfully")

if __name__ == "__main__":
    main()
