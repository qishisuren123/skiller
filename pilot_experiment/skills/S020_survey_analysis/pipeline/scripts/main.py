import argparse
import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description='Analyze Likert-scale survey responses')
    parser.add_argument('--input', required=True, help='Path to input CSV file')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--reverse-items', default='q3,q5,q7', 
                       help='Comma-separated list of items to reverse-code')
    return parser.parse_args()

def reverse_code_items(df, reverse_items):
    """Reverse code specified items: 6 - original_value"""
    df_copy = df.copy()
    for item in reverse_items:
        if item in df_copy.columns:
            df_copy[f'{item}_r'] = 6 - df_copy[item]
    return df_copy

def compute_composite_scores(df, reverse_items):
    """Compute scale_A and scale_B composite scores"""
    # For scale_A (q1-q5), use reverse-coded versions where applicable
    scale_a_cols = []
    for i in range(1, 6):
        item = f'q{i}'
        if item in reverse_items and f'{item}_r' in df.columns:
            scale_a_cols.append(f'{item}_r')
        else:
            scale_a_cols.append(item)
    
    # For scale_B (q6-q10), use reverse-coded versions where applicable  
    scale_b_cols = []
    for i in range(6, 11):
        item = f'q{i}'
        if item in reverse_items and f'{item}_r' in df.columns:
            scale_b_cols.append(f'{item}_r')
        else:
            scale_b_cols.append(item)
    
    df['scale_A'] = df[scale_a_cols].mean(axis=1)
    df['scale_B'] = df[scale_b_cols].mean(axis=1)
    
    return df, scale_a_cols, scale_b_cols

def cronbach_alpha(df, items):
    """Calculate Cronbach's alpha for a set of items"""
    item_data = df[items].dropna()
    k = len(items)
    
    if k < 2:
        return np.nan
    
    # Calculate correlation matrix for numerical stability
    corr_matrix = item_data.corr()
    
    # Average inter-item correlation
    sum_correlations = corr_matrix.sum().sum() - k  # subtract diagonal
    avg_correlation = sum_correlations / (k * (k - 1))
    
    # Spearman-Brown formula (equivalent to Cronbach's alpha)
    alpha = (k * avg_correlation) / (1 + (k - 1) * avg_correlation)
    
    return alpha

def group_comparison(df):
    """Perform group comparison by gender"""
    comparison = {}
    
    for gender in df['gender'].unique():
        gender_data = df[df['gender'] == gender]
        comparison[gender] = {
            'scale_A_mean': gender_data['scale_A'].mean(),
            'scale_A_std': gender_data['scale_A'].std(),
            'scale_B_mean': gender_data['scale_B'].mean(), 
            'scale_B_std': gender_data['scale_B'].std(),
            'n': len(gender_data)
        }
    
    return comparison

def main():
    args = parse_arguments()
    
    # Parse reverse items
    reverse_items = [item.strip() for item in args.reverse_items.split(',')]
    
    # Load data
    df = pd.read_csv(args.input)
    
    # Reverse code items
    df = reverse_code_items(df, reverse_items)
    
    # Compute composite scores
    df, scale_a_items, scale_b_items = compute_composite_scores(df, reverse_items)
    
    # Calculate Cronbach's alpha
    alpha_a = cronbach_alpha(df, scale_a_items)
    alpha_b = cronbach_alpha(df, scale_b_items)
    
    # Group comparison
    comparison = group_comparison(df)
    
    # Create output directory
    Path(args.output).mkdir(parents=True, exist_ok=True)
    
    # Save outputs
    df.to_csv(os.path.join(args.output, 'recoded_responses.csv'), index=False)
    
    # Reliability output
    reliability = {
        'scale_A': {'alpha': alpha_a, 'n_items': len(scale_a_items), 'items': scale_a_items},
        'scale_B': {'alpha': alpha_b, 'n_items': len(scale_b_items), 'items': scale_b_items}
    }
    
    with open(os.path.join(args.output, 'reliability.json'), 'w') as f:
        json.dump(reliability, f, indent=2)
    
    with open(os.path.join(args.output, 'group_comparison.json'), 'w') as f:
        json.dump(comparison, f, indent=2)
    
    # Print results
    print(f"Cronbach's alpha - Scale A: {alpha_a:.3f}")
    print(f"Cronbach's alpha - Scale B: {alpha_b:.3f}")
    
    for gender, stats in comparison.items():
        print(f"\n{gender} group (n={stats['n']}):")
        print(f"  Scale A: {stats['scale_A_mean']:.2f} ± {stats['scale_A_std']:.2f}")
        print(f"  Scale B: {stats['scale_B_mean']:.2f} ± {stats['scale_B_std']:.2f}")

if __name__ == '__main__':
    main()
