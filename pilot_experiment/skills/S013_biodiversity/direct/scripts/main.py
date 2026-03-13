#!/usr/bin/env python3
"""
Biodiversity Indices Calculator
Calculates standard ecological diversity indices from species abundance matrices.
"""

import argparse
import pandas as pd
import numpy as np
import sys
from pathlib import Path

def calculate_species_richness(abundances):
    """Calculate species richness (number of species present)"""
    return np.sum(abundances > 0)

def calculate_shannon_diversity(abundances):
    """Calculate Shannon diversity index H' = -Σ(pi * ln(pi))"""
    # Filter out zero abundances
    present_species = abundances[abundances > 0]
    if len(present_species) == 0:
        return 0.0
    
    total_abundance = present_species.sum()
    proportions = present_species / total_abundance
    return -np.sum(proportions * np.log(proportions))

def calculate_simpson_diversity(abundances):
    """Calculate Simpson diversity index 1-D where D = Σ(pi²)"""
    present_species = abundances[abundances > 0]
    if len(present_species) == 0:
        return 0.0
    
    total_abundance = present_species.sum()
    proportions = present_species / total_abundance
    simpson_dominance = np.sum(proportions ** 2)
    return 1 - simpson_dominance

def calculate_pielou_evenness(abundances):
    """Calculate Pielou evenness J = H'/ln(S)"""
    richness = calculate_species_richness(abundances)
    if richness <= 1:
        return 0.0  # Evenness undefined for 0 or 1 species
    
    shannon = calculate_shannon_diversity(abundances)
    return shannon / np.log(richness)

def calculate_total_abundance(abundances):
    """Calculate total abundance (sum of all individuals)"""
    return abundances.sum()

def calculate_biodiversity_indices(abundance_matrix, indices_to_calculate):
    """Calculate specified biodiversity indices for all sites"""
    results = []
    
    for site_idx, site_row in abundance_matrix.iterrows():
        site_data = {'site_id': site_idx}
        abundances = site_row.values
        
        if 'richness' in indices_to_calculate or 'all' in indices_to_calculate:
            site_data['species_richness'] = calculate_species_richness(abundances)
        
        if 'shannon' in indices_to_calculate or 'all' in indices_to_calculate:
            site_data['shannon_diversity'] = round(calculate_shannon_diversity(abundances), 4)
        
        if 'simpson' in indices_to_calculate or 'all' in indices_to_calculate:
            site_data['simpson_diversity'] = round(calculate_simpson_diversity(abundances), 4)
        
        if 'evenness' in indices_to_calculate or 'all' in indices_to_calculate:
            site_data['pielou_evenness'] = round(calculate_pielou_evenness(abundances), 4)
        
        if 'abundance' in indices_to_calculate or 'all' in indices_to_calculate:
            site_data['total_abundance'] = calculate_total_abundance(abundances)
        
        results.append(site_data)
    
    return pd.DataFrame(results)

def print_summary(abundance_matrix, results_df):
    """Print ecological summary statistics"""
    total_sites = len(abundance_matrix)
    total_species = np.sum((abundance_matrix > 0).any(axis=0))
    
    print(f"\n=== Biodiversity Analysis Summary ===")
    print(f"Total sampling sites: {total_sites}")
    print(f"Total species recorded: {total_species}")
    
    if 'shannon_diversity' in results_df.columns:
        mean_shannon = results_df['shannon_diversity'].mean()
        print(f"Mean Shannon diversity: {mean_shannon:.4f}")
        
        most_diverse_idx = results_df['shannon_diversity'].idxmax()
        most_diverse_site = results_df.loc[most_diverse_idx, 'site_id']
        max_shannon = results_df.loc[most_diverse_idx, 'shannon_diversity']
        print(f"Most diverse site: {most_diverse_site} (H' = {max_shannon:.4f})")

def validate_abundance_data(df):
    """Validate that abundance data is appropriate for ecological analysis"""
    # Check for negative values
    if (df < 0).any().any():
        raise ValueError("Negative abundance values detected - biologically impossible")
    
    # Check if all values are numeric
    if not df.select_dtypes(include=[np.number]).shape[1] == df.shape[1]:
        raise ValueError("Non-numeric values detected in abundance matrix")
    
    # Warn if all sites are empty
    if df.sum().sum() == 0:
        print("Warning: All sites have zero abundance")

def main():
    parser = argparse.ArgumentParser(
        description="Calculate biodiversity indices from species abundance matrix"
    )
    parser.add_argument(
        "--input", 
        required=True, 
        help="Input CSV file with sites as rows, species as columns"
    )
    parser.add_argument(
        "--output", 
        required=True, 
        help="Output CSV file for biodiversity indices"
    )
    parser.add_argument(
        "--indices", 
        default="all",
        help="Indices to calculate: all, richness, shannon, simpson, evenness, abundance (comma-separated)"
    )
    
    args = parser.parse_args()
    
    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    
    try:
        # Load abundance matrix
        print(f"Loading abundance data from {args.input}...")
        abundance_matrix = pd.read_csv(args.input, index_col=0)
        
        # Validate data
        validate_abundance_data(abundance_matrix)
        
        # Parse indices to calculate
        if args.indices.lower() == "all":
            indices_to_calculate = ["all"]
        else:
            indices_to_calculate = [idx.strip().lower() for idx in args.indices.split(",")]
        
        print(f"Calculating biodiversity indices...")
        
        # Calculate indices
        results = calculate_biodiversity_indices(abundance_matrix, indices_to_calculate)
        
        # Save results
        results.to_csv(args.output, index=False)
        print(f"Results saved to {args.output}")
        
        # Print summary
        print_summary(abundance_matrix, results)
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
