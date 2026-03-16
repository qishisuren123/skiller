#!/usr/bin/env python3
import argparse
import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict, Counter
import logging

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_interaction_data(file_path):
    """Parse interaction data from CSV file"""
    try:
        df = pd.read_csv(file_path)
        required_columns = ['user_id', 'interaction_type', 'timestamp', 'target_user']
        
        if not all(col in df.columns for col in required_columns):
            raise ValueError(f"Missing required columns. Expected: {required_columns}")
        
        # Convert timestamp to datetime with ISO format handling
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601')
        
        logging.info(f"Loaded {len(df)} interactions from {file_path}")
        return df
    except Exception as e:
        logging.error(f"Error parsing data: {e}")
        raise

def calculate_influence_scores(df):
    """Calculate weighted influence scores for each user using vectorized operations"""
    logging.info("Calculating influence scores...")
    
    # Define interaction weights
    weights = {'share': 3, 'comment': 2, 'like': 1}
    
    # Map weights to dataframe
    df_weighted = df.copy()
    df_weighted['weight'] = df_weighted['interaction_type'].map(weights).fillna(0)
    
    # Group by user and sum weights
    influence_scores = df_weighted.groupby('user_id')['weight'].sum().to_dict()
    
    return influence_scores

def calculate_degree_centrality(df):
    """Calculate normalized degree centrality using optimized pandas operations"""
    logging.info("Calculating degree centrality...")
    
    # Remove any rows with NaN values in user columns
    clean_df = df.dropna(subset=['user_id', 'target_user'])
    
    if len(clean_df) == 0:
        logging.warning("No valid user interactions found after cleaning")
        return {}
    
    # Create edges dataframe for both directions
    edges = clean_df[['user_id', 'target_user']].drop_duplicates()
    
    # Get all unique users
    all_users = set(clean_df['user_id']).union(set(clean_df['target_user']))
    
    if len(all_users) == 0:
        logging.warning("No users found in dataset")
        return {}
    
    # Count unique connections for each user (outgoing)
    outgoing_counts = edges.groupby('user_id')['target_user'].nunique()
    
    # Count unique connections for each user (incoming) 
    incoming_counts = edges.groupby('target_user')['user_id'].nunique()
    
    # Create a series for all users initialized to 0
    user_connections = pd.Series(0, index=list(all_users), dtype=int)
    
    # Add outgoing connections
    if not outgoing_counts.empty:
        user_connections = user_connections.add(outgoing_counts, fill_value=0)
    
    # Add incoming connections (rename index to match)
    if not incoming_counts.empty:
        incoming_counts.index.name = None  # Remove index name
        user_connections = user_connections.add(incoming_counts, fill_value=0)
    
    # Normalize by maximum possible connections
    max_possible_connections = len(all_users) - 1
    
    if max_possible_connections > 0:
        centrality_scores = (user_connections / max_possible_connections).to_dict()
    else:
        centrality_scores = {user: 0 for user in all_users}
    
    logging.info(f"Calculated centrality for {len(centrality_scores)} users")
    return centrality_scores

def normalize_scores(scores):
    """Normalize scores to [0, 1] range using min-max normalization"""
    if not scores:
        return scores
    
    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        # All values are the same, return uniform distribution
        return {user: 1.0 for user in scores}
    
    normalized = {}
    for user, score in scores.items():
        normalized[user] = (score - min_val) / (max_val - min_val)
    
    return normalized

def calculate_combined_scores(influence_scores, centrality_scores):
    """Calculate combined influence metric (60% influence, 40% centrality)"""
    logging.info("Calculating combined scores...")
    
    # Normalize influence scores to [0, 1] range
    normalized_influence = normalize_scores(influence_scores)
    
    all_users = set(normalized_influence.keys()).union(set(centrality_scores.keys()))
    combined_scores = {}
    
    for user in all_users:
        influence = normalized_influence.get(user, 0)
        centrality = centrality_scores.get(user, 0)
        combined_scores[user] = 0.6 * influence + 0.4 * centrality
    
    return combined_scores

def analyze_interactions(df):
    """Compute interaction summary statistics using vectorized operations"""
    logging.info("Computing interaction statistics...")
    
    # Count interactions by type
    interaction_counts = df['interaction_type'].value_counts().to_dict()
    
    # Calculate time period
    start_date = df['timestamp'].min()
    end_date = df['timestamp'].max()
    time_period_days = (end_date - start_date).days + 1
    
    # Calculate averages
    total_users = df['user_id'].nunique() + df['target_user'].nunique() - len(set(df['user_id']).intersection(set(df['target_user'])))
    total_interactions = len(df)
    avg_interactions_per_user = total_interactions / total_users
    interaction_rate_per_day = total_interactions / time_period_days
    
    return {
        'total_interactions_by_type': interaction_counts,
        'total_interactions': total_interactions,
        'total_users': total_users,
        'average_interactions_per_user': avg_interactions_per_user,
        'interaction_rate_per_day': interaction_rate_per_day,
        'time_period_days': time_period_days,
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat()
    }

def generate_output(influence_scores, centrality_scores, combined_scores, interaction_stats, top_n):
    """Generate complete analysis output"""
    # Normalize influence scores for output consistency
    normalized_influence = normalize_scores(influence_scores)
    
    # Get top influencers
    top_influencers = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    # Prepare individual user metrics
    all_users = set(influence_scores.keys()).union(set(centrality_scores.keys()))
    user_metrics = {}
    
    for user in all_users:
        user_metrics[str(user)] = {
            'raw_influence_score': influence_scores.get(user, 0),
            'normalized_influence_score': normalized_influence.get(user, 0),
            'centrality_score': centrality_scores.get(user, 0),
            'combined_score': combined_scores.get(user, 0)
        }
    
    # Prepare top influencers list
    top_influencers_list = []
    for rank, (user_id, score) in enumerate(top_influencers, 1):
        top_influencers_list.append({
            'rank': rank,
            'user_id': str(user_id),
            'combined_score': score,
            'raw_influence_score': influence_scores.get(user_id, 0),
            'normalized_influence_score': normalized_influence.get(user_id, 0),
            'centrality_score': centrality_scores.get(user_id, 0)
        })
    
    return {
        'top_influencers': top_influencers_list,
        'user_metrics': user_metrics,
        'network_summary': interaction_stats
    }

def main():
    parser = argparse.ArgumentParser(description='Social Network Influence Analysis')
    parser.add_argument('input_file', help='Path to CSV file containing interaction data')
    parser.add_argument('--output', '-o', default='influence_analysis.json', 
                       help='Output JSON file path')
    parser.add_argument('--top-n', '-n', type=int, default=10, 
                       help='Number of top influencers to identify')
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        # Parse data
        df = parse_interaction_data(args.input_file)
        
        # Calculate metrics
        influence_scores = calculate_influence_scores(df)
        centrality_scores = calculate_degree_centrality(df)
        combined_scores = calculate_combined_scores(influence_scores, centrality_scores)
        
        # Analyze interactions
        interaction_stats = analyze_interactions(df)
        
        # Generate output
        results = generate_output(influence_scores, centrality_scores, combined_scores, 
                                interaction_stats, args.top_n)
        
        # Save to JSON file
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary to console
        print(f"\nSocial Network Influence Analysis Results")
        print(f"=========================================")
        print(f"Total interactions: {interaction_stats['total_interactions']}")
        print(f"Total users: {interaction_stats['total_users']}")
        print(f"Time period: {interaction_stats['time_period_days']} days")
        print(f"Interaction rate: {interaction_stats['interaction_rate_per_day']:.2f} per day")
        
        print(f"\nTop {args.top_n} Influencers:")
        for influencer in results['top_influencers']:
            print(f"{influencer['rank']}. User {influencer['user_id']}: "
                  f"Combined Score = {influencer['combined_score']:.3f} "
                  f"(Influence: {influencer['normalized_influence_score']:.3f}, "
                  f"Centrality: {influencer['centrality_score']:.3f})")
        
        print(f"\nDetailed results saved to: {args.output}")
        logging.info("Analysis completed successfully")
        
    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
