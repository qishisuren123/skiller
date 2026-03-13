# Example 1: Basic influence analysis with sample data
import pandas as pd
import json

# Sample interaction data
sample_data = pd.DataFrame({
    'user_id': ['user1', 'user2', 'user3', 'user1', 'user2'],
    'target_user': ['user2', 'user3', 'user1', 'user3', 'user1'],
    'interaction_type': ['share', 'like', 'comment', 'like', 'share'],
    'timestamp': ['2024-01-01', '2024-01-02', '2024-01-02', '2024-01-03', '2024-01-03']
})

# Calculate influence scores
weights = {'share': 3, 'comment': 2, 'like': 1}
sample_data['weight'] = sample_data['interaction_type'].map(weights)
influence_scores = sample_data.groupby('user_id')['weight'].sum()

print("Influence Scores:")
print(influence_scores.sort_values(ascending=False))
# Output: user1: 4, user2: 4, user3: 2

# Example 2: Complete network analysis pipeline
def analyze_sample_network():
    # Load data
    interactions = pd.DataFrame({
        'user_id': ['A', 'B', 'C', 'A', 'B', 'C', 'D'],
        'target_user': ['B', 'C', 'A', 'D', 'A', 'D', 'A'],
        'interaction_type': ['share', 'share', 'comment', 'like', 'comment', 'like', 'share'],
        'timestamp': pd.to_datetime(['2024-01-01', '2024-01-01', '2024-01-02', 
                                   '2024-01-02', '2024-01-03', '2024-01-03', '2024-01-04'])
    })
    
    # Calculate metrics
    weights = {'share': 3, 'comment': 2, 'like': 1}
    interactions['weight'] = interactions['interaction_type'].map(weights)
    
    # Influence scores
    influence = interactions.groupby('user_id')['weight'].sum()
    
    # Degree centrality
    connections = pd.concat([
        interactions[['user_id', 'target_user']].rename(columns={'target_user': 'connected'}),
        interactions[['target_user', 'user_id']].rename(columns={'target_user': 'user_id', 'user_id': 'connected'})
    ])
    centrality = connections.groupby('user_id')['connected'].nunique()
    centrality_norm = (centrality - centrality.min()) / (centrality.max() - centrality.min())
    
    # Combined score
    influence_norm = (influence - influence.min()) / (influence.max() - influence.min())
    combined = 0.6 * influence_norm + 0.4 * centrality_norm
    
    results = {
        'top_influencers': [
            {'user_id': user, 'combined_score': float(score)} 
            for user, score in combined.sort_values(ascending=False).items()
        ]
    }
    
    return results

# Run analysis
results = analyze_sample_network()
print(json.dumps(results, indent=2))
