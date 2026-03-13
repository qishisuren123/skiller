import argparse
import pandas as pd
import numpy as np
import math
import sys

def validate_abundance_data(df):
    """Validate the abundance data for common issues"""
    issues = []
    
    # Check for negative values
    negative_mask = df < 0
    if negative_mask.any().any():
        neg_locations = negative_mask.stack()
        neg_sites = neg_locations[neg_locations].index.get_level_values(0).unique()
        issues.append(f"Negative values found in sites: {list(neg_sites)}")
    
    # Check for non-numeric data
    non_numeric = df.select_dtypes(exclude=[np.number]).columns
    if len(non_numeric) > 0:
        issues.append(f"Non-numeric columns found: {list(non_numeric)}")
    
    # Check for sites with all zeros
    zero_sites = df.index[(df == 0).all(axis=1)]
    if len(zero_sites) > 0:
        issues.append(f"Sites with all zero abundances: {list(zero_sites)}")
    
    # Check for completely empty species (all zeros)
    zero_species = df.columns[(df == 0).all(axis=0)]
    if len(zero_species) > 0:
        issues.append(f"Species with zero abundance across all sites: {list(zero_species)}")
    
    return issues

def calculate_shannon_diversity(abundances):
    """Calculate Shannon diversity index (H')"""
    # Convert to absolute values and filter negatives
    abundances = [max(0, x) for x in abundances]
    total = sum(abundances)
    
    if total == 0:
        return 0
    
    shannon = 0
    for count in abundances:
        if count > 0:
            p = count / total
            shannon += p * math.log(p)
    
    return -shannon

def calculate_simpson_diversity(abundances):
    """Calculate Simpson diversity index (1-D)"""
    # Convert to absolute values and filter negatives
    abundances = [max(0, x) for x in abundances]
    total = sum(abundances)
    
    if total == 0:
        return 0
    
    simpson_d = 0
    for count in abundances:
        if count > 0:
            p = count / total
            simpson_d += p * p
    
    return 1 - simpson_d

def calculate_pielou_evenness(shannon, richness):
    """Calculate Pielou evenness (J)"""
    if richness <= 1:
        return 0
    return shannon / math.log(richness)

def calculate_biodiversity_indices(abundance_row, indices_to_calc):
    """Calculate specified biodiversity indices for a site"""
    results = {}
    
    # Handle negative values by converting to zero with warning
    clean_abundances = [max(0, x) for x in abundance_row]
    
    # Always calculate basic metrics as they're needed for other calculations
    richness = sum(1 for x in clean_abundances if x > 0)
    total_abundance = sum(clean_abundances)
    
    # Handle case where site has no species
    if total_abundance == 0:
        if 'richness' in indices_to_calc:
            results['species_richness'] = 0
        if 'abundance' in indices_to_calc:
            results['total_abundance'] = 0
        if 'shannon' in indices_to_calc:
            results['shannon_diversity'] = 0
        if 'simpson' in indices_to_calc:
            results['simpson_diversity'] = 0
        if 'evenness' in indices_to_calc:
            results['pielou_evenness'] = 0
        return results
    
    if 'richness' in indices_to_calc:
        results['species_richness'] = richness
    
    if 'abundance' in indices_to_calc:
        results['total_abundance'] = total_abundance
    
    # Shannon diversity
    shannon = None
    if 'shannon' in indices_to_calc or 'evenness' in indices_to_calc:
        shannon = calculate_shannon_diversity(clean_abundances)
        if 'shannon' in indices_to_calc:
            results['shannon_diversity'] = shannon
    
    # Simpson diversity
    if 'simpson' in indices_to_calc:
        simpson = calculate_simpson_diversity(clean_abundances)
        results['simpson_diversity'] = simpson
    
    # Pielou evenness (needs Shannon)
    if 'evenness' in indices_to_calc:
        if shannon is None:
            shannon = calculate_shannon_diversity(clean_abundances)
        pielou = calculate_pielou_evenness(shannon, richness)
        results['pielou_evenness'] = pielou
    
    return results

def parse_indices(indices_str):
    """Parse the indices parameter"""
    if indices_str.lower() == 'all':
        return ['richness', 'shannon', 'simpson', 'evenness', 'abundance']
    
    valid_indices = ['richness', 'shannon', 'simpson', 'evenness', 'abundance']
    requested = [idx.strip().lower() for idx in indices_str.split(',')]
    
    invalid = [idx for idx in requested if idx not in valid_indices]
    if invalid:
        raise ValueError(f"Invalid indices: {invalid}. Valid options: {valid_indices}")
    
    return requested

def main():
    parser = argparse.ArgumentParser(description='Calculate biodiversity indices')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', required=True, help='Output CSV file')
    parser.add_argument('--indices', default='all', 
                       help='Comma-separated indices to calculate: richness,shannon,simpson,evenness,abundance (default: all)')
    
    args = parser.parse_args()
    
    try:
        # Parse which indices to calculate
        indices_to_calc = parse_indices(args.indices)
        
        # Read input data
        df = pd.read_csv(args.input, index_col=0)
        
        # Validate data and report issues
        issues = validate_abundance_data(df)
        if issues:
            print("Data validation warnings:")
            for issue in issues:
                print(f"  - {issue}")
            print()
        
        # Calculate indices for each site
        results = []
        for site_id, row in df.iterrows():
            indices = calculate_biodiversity_indices(row.values, indices_to_calc)
            indices['site_id'] = site_id
            results.append(indices)
        
        # Create output dataframe with proper column ordering
        results_df = pd.DataFrame(results)
        
        # Define column order: site_id first, then indices in logical order
        column_order = ['site_id']
        column_mapping = {
            'richness': 'species_richness',
            'abundance': 'total_abundance', 
            'shannon': 'shannon_diversity',
            'simpson': 'simpson_diversity',
            'evenness': 'pielou_evenness'
        }
        
        for idx in ['richness', 'abundance', 'shannon', 'simpson', 'evenness']:
            if idx in indices_to_calc and column_mapping[idx] in results_df.columns:
                column_order.append(column_mapping[idx])
        
        # Reorder columns and save
        results_df = results_df[column_order]
        results_df.to_csv(args.output, index=False)
        
        # Print summary statistics
        total_sites = len(results)
        total_species = (df > 0).any().sum()
        
        if total_sites > 0:
            if 'shannon' in indices_to_calc:
                mean_shannon = results_df['shannon_diversity'].mean()
                most_diverse_idx = results_df['shannon_diversity'].idxmax()
                most_diverse_site = results_df.loc[most_diverse_idx, 'site_id']
                
                print(f"Summary:")
                print(f"Total sites: {total_sites}")
                print(f"Total species: {total_species}")
                print(f"Mean Shannon diversity: {mean_shannon:.3f}")
                print(f"Most diverse site: {most_diverse_site}")
            else:
                print(f"Summary:")
                print(f"Total sites: {total_sites}")
                print(f"Total species: {total_species}")
                print("(Shannon diversity not calculated)")
        else:
            print("No sites found in dataset")
            
    except FileNotFoundError:
        print(f"Error: Input file '{args.input}' not found")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
