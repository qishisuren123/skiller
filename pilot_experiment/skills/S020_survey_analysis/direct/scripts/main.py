import pandas as pd
import numpy as np
import argparse
import json
import os
from pathlib import Path

def cronbach_alpha(items_df):
    """Calculate Cronbach's alpha reliability coefficient"""
    k = len(items_df.columns)
    if k < 2:
        return 0.0
    
    item_variances = items_df.var(axis=0, ddof=1).sum()
    total_variance = items_df.sum(axis=1).var(ddof=1)
    
    if total_variance == 0:
        return 0.0
    
    alpha = (k / (k - 1)) * (1 - item_variances / total_variance)
    return alpha

def reverse_code_items(df, items_to_reverse):
    """Apply reverse coding: new_value = 6 - original_value"""
    df_recoded = df.copy()
    
    for item in items_to_reverse:
        if item in df.columns:
            reversed_col = f"{item}_r"
            df_recoded[reversed_col] = 6 - df[item]
            # Replace original with reversed for composite calculations
            df_recoded[item] = df_recoded[reversed_col]
    
    return df_recoded

def calculate_composite_scores(df):
    """Calculate scale_A (q1-q5) and scale_B (q6-q10) composite scores"""
    scale_a_items = [f'q{i}' for i in range(1, 6)]
    scale_b_items = [f'q{i}' for i in range(6, 11)]
    
    df['scale_A'] = df[scale_a_items].mean(axis=1)
    df['scale_B'] = df[scale_b_items].mean(axis=1)
    
    return df

def analyze_reliability(df):
    """Compute Cronbach's alpha for both scales"""
    scale_a_items = [f'q{i}' for i in range(1, 6)]
    scale_b_items = [f'q{i}' for i in range(6, 11)]
    
    alpha_a = cronbach_alpha(df[scale_a_items])
    alpha_b = cronbach_alpha(df[scale_b_items])
    
    reliability = {
        'scale_A': {
            'alpha': round(alpha_a, 3),
            'n_items': len(scale_a_items),
            'items': scale_a_items
        },
        'scale_B': {
            'alpha': round(alpha_b, 3),
            'n_items': len(scale_b_items),
            'items': scale_b_items
        }
    }
    
    return reliability

def group_comparison(df):
    """Perform demographic analysis by gender groups"""
    comparison = {}
    
    for gender in df['gender'].unique():
        if pd.isna(gender):
            continue
            
        group_data = df[df['gender'] == gender]
        
        comparison[gender] = {
            'scale_A_mean': round(group_data['scale_A'].mean(), 3),
            'scale_A_std': round(group_data['scale_A'].std(ddof=1), 3),
            'scale_B_mean': round(group_data['scale_B'].mean(), 3),
            'scale_B_std': round(group_data['scale_B'].std(ddof=1), 3),
            'n': len(group_data)
        }
    
    return comparison

def main():
    parser = argparse.ArgumentParser(description='Analyze Likert-scale survey responses')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output', required=True, help='Output directory path')
    parser.add_argument('--reverse-items', default='q3,q5,q7', 
                       help='Comma-separated list of items to reverse-code')
    
    args = parser.parse_args()
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # Load data
    try:
        df = pd.read_csv(args.input)
    except FileNotFoundError:
        print(f"Error: Input file {args.input} not found")
        return
    
    # Validate required columns
    required_cols = ['respondent_id', 'age', 'gender'] + [f'q{i}' for i in range(1, 11)]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing required columns: {missing_cols}")
        return
    
    # Validate Likert scale values
    likert_cols = [f'q{i}' for i in range(1, 11)]
    for col in likert_cols:
        if not df[col].between(1, 5).all():
            print(f"Warning: Column {col} contains values outside 1-5 range")
    
    # Parse reverse items
    reverse_items = [item.strip() for item in args.reverse_items.split(',')]
    
    # Apply reverse coding
    df_recoded = reverse_code_items(df, reverse_items)
    
    # Calculate composite scores
    df_final = calculate_composite_scores(df_recoded)
    
    # Reliability analysis
    reliability = analyze_reliability(df_final)
    
    # Group comparison
    groups = group_comparison(df_final)
    
    # Save outputs
    df_final.to_csv(os.path.join(args.output, 'recoded_responses.csv'), index=False)
    
    with open(os.path.join(args.output, 'reliability.json'), 'w') as f:
        json.dump(reliability, f, indent=2)
    
    with open(os.path.join(args.output, 'group_comparison.json'), 'w') as f:
        json.dump(groups, f, indent=2)
    
    # Print summary
    print("=== RELIABILITY ANALYSIS ===")
    print(f"Scale A Cronbach's Alpha: {reliability['scale_A']['alpha']}")
    print(f"Scale B Cronbach's Alpha: {reliability['scale_B']['alpha']}")
    
    print("\n=== GROUP MEANS ===")
    for gender, stats in groups.items():
        print(f"{gender} (n={stats['n']}):")
        print(f"  Scale A: M={stats['scale_A_mean']}, SD={stats['scale_A_std']}")
        print(f"  Scale B: M={stats['scale_B_mean']}, SD={stats['scale_B_std']}")

if __name__ == "__main__":
    main()
