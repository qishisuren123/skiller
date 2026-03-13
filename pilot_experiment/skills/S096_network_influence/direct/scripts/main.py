import pandas as pd
import numpy as np
import json
import argparse
from datetime import datetime
from collections import defaultdict
import sys

def load_interaction_data(filepath):
    """Load and validate interaction data from CSV or JSON file."""
    try:
        if filepath.endswith('.json'):
            df = pd.read_json(filepath)
        else:
            df = pd.read_csv(filepath)
        
        required_columns = ['user_id', 'target_user', 'interaction_type', 'timestamp']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Parse timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp'])
        
        # Remove self-interactions
        df = df[df['user_id'] != df['target_user']]
        
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        sys.exit(1)

def calculate_influence_scores(interactions_df):
    """Calculate weighted influence scores for each user."""
    weights = {'share': 3, 'comment': 2, 'like': 1}
    
    # Apply weights with fallback for unknown interaction types
    interactions_df['weight'] = interactions_df['interaction_type'].map(
        lambda x: weights.get(x, 1)
    )
    
    # Sum weighted interactions per user
    influence_scores = interactions_df.groupby('user_id')['weight'].sum()
    return influence_scores

def calculate_degree_centrality(interactions_df):
    """Calculate normalized degree centrality for each user."""
    # Create bidirectional connections
    outgoing = interactions_df[['user_id', 'target_user']].rename(
        columns={'target_user': 'connected_user'}
    )
    incoming = interactions_df[['target_user', 'user_id']].rename(
        columns={'target_user': 'user_id', 'user_id': 'connected_user'}
    )
    
    all_connections = pd.concat([outgoing, incoming])
    
    # Count unique connections per user
    degree_counts = all_connections.groupby('user_id')['connected_user'].nunique()
    
    # Normalize to [0, 1] range
    if len(degree_counts) > 1 and degree_counts.max() > degree_counts.min():
        centrality_norm = (degree_counts - degree_counts.min()) / (
            degree_counts.max() - degree_counts.min()
        )
    else:
        centrality_norm = pd.Series(1.0, index=degree_counts.index)
    
    return centrality_norm

def compute_network_statistics(interactions_df):
    """Compute summary statistics for the network."""
    total_interactions = len(interactions_df)
    unique_users = pd.concat([interactions_df['user_id'], interactions_df['target_user']]).nunique()
    
    # Interaction type breakdown
    interaction_counts = interactions_df['interaction_type'].value_counts().to_dict()
    
    # Time period analysis
    time_span = (interactions_df['timestamp'].max() - interactions_df['timestamp'].min()).days
    if time_span == 0:
        time_span = 1  # Avoid division by zero
    
    interactions_per_day = total_interactions / time_span
    avg_interactions_per_user = total_interactions / unique_users if unique_users > 0 else 0
    
    return {
        'total_interactions': int(total_interactions),
        'unique_users': int(unique_users),
        'interaction_types': interaction_counts,
        'time_span_days': int(time_span),
        'interactions_per_day': round(interactions_per_day, 2),
        'avg_interactions_per_user': round(avg_interactions_per_user, 2)
    }

def identify_top_influencers(interactions_df, top_n=10):
    """Identify top N influencers based on combined influence metric."""
    # Calculate component metrics
    influence_scores = calculate_influence_scores(interactions_df)
    centrality_scores = calculate_degree_centrality(interactions_df)
    
    # Normalize influence scores to [0, 1]
    if len(influence_scores) > 1 and influence_scores.max() > influence_scores.min():
        influence_norm = (influence_scores - influence_scores.min()) / (
            influence_scores.max() - influence_scores.min()
        )
    else:
        influence_norm = pd.Series(1.0, index=influence_scores.index)
    
    # Align indices for users present in both metrics
    common_users = influence_norm.index.intersection(centrality_scores.index)
    influence_aligned = influence_norm.loc[common_users]
    centrality_aligned = centrality_scores.loc[common_users]
    
    # Combined metric: 60% influence, 40% centrality
    combined_scores = 0.6 * influence_aligned + 0.4 * centrality_aligned
    
    # Get top N influencers
    top_influencers = combined_scores.sort_values(ascending=False).head(top_n)
    
    # Prepare detailed results
    results = []
    for user_id in top_influencers.index:
        results.append({
            'user_id': str(user_id),
            'combined_score': round(float(combined_scores[user_id]), 4),
            'influence_score': round(float(influence_scores.get(user_id, 0)), 2),
            'centrality_score': round(float(centrality_scores.get(user_id, 0)), 4),
            'raw_influence': int(influence_scores.get(user_id, 0))
        })
    
    return results

def main():
    parser = argparse.ArgumentParser(description='Analyze social network influence')
    parser.add_argument('input_file', help='Input CSV or JSON file with interaction data')
    parser.add_argument('-n', '--top-n', type=int, default=10, 
                       help='Number of top influencers to identify (default: 10)')
    parser.add_argument('-o', '--output', default='influence_analysis.json',
                       help='Output JSON file (default: influence_analysis.json)')
    
    args = parser.parse_args()
    
    print("Loading interaction data...")
    interactions_df = load_interaction_data(args.input_file)
    
    if len(interactions_df) == 0:
        print("No valid interactions found in the dataset.")
        sys.exit(1)
    
    print(f"Analyzing {len(interactions_df)} interactions...")
    
    # Perform analysis
    top_influencers = identify_top_influencers(interactions_df, args.top_n)
    network_stats = compute_network_statistics(interactions_df)
    
    # Prepare final results
    results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'top_influencers': top_influencers,
        'network_statistics': network_stats,
        'parameters': {
            'top_n': args.top_n,
            'influence_weight': 0.6,
            'centrality_weight': 0.4,
            'interaction_weights': {'share': 3, 'comment': 2, 'like': 1}
        }
    }
    
    # Save results
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nTop {args.top_n} Influencers:")
    print("-" * 60)
    for i, influencer in enumerate(top_influencers, 1):
        print(f"{i:2d}. User {influencer['user_id']:>8} | "
              f"Score: {influencer['combined_score']:.4f} | "
              f"Influence: {influencer['raw_influence']:>3d} | "
              f"Centrality: {influencer['centrality_score']:.4f}")
    
    print(f"\nNetwork Statistics:")
    print(f"Total interactions: {network_stats['total_interactions']:,}")
    print(f"Unique users: {network_stats['unique_users']:,}")
    print(f"Interactions per day: {network_stats['interactions_per_day']:.1f}")
    print(f"\nResults saved to: {args.output}")

if __name__ == "__main__":
    main()
