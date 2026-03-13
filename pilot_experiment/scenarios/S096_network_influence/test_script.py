import subprocess
import json
import tempfile
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def create_data():
    """Generate synthetic social network interaction data"""
    np.random.seed(42)
    
    # Generate users
    n_users = 50
    users = [f"user_{i:03d}" for i in range(n_users)]
    
    # Generate interactions over 30 days
    start_date = datetime(2024, 1, 1)
    interactions = []
    
    # Create some power users (influencers)
    power_users = users[:5]
    regular_users = users[5:30]
    casual_users = users[30:]
    
    interaction_types = ['like', 'share', 'comment']
    
    # Power users generate many interactions
    for user in power_users:
        n_interactions = np.random.randint(80, 120)
        for _ in range(n_interactions):
            target = np.random.choice([u for u in users if u != user])
            interaction_type = np.random.choice(interaction_types, p=[0.5, 0.3, 0.2])
            timestamp = start_date + timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            interactions.append({
                'user_id': user,
                'target_user': target,
                'interaction_type': interaction_type,
                'timestamp': timestamp.isoformat()
            })
    
    # Regular users
    for user in regular_users:
        n_interactions = np.random.randint(20, 50)
        for _ in range(n_interactions):
            target = np.random.choice([u for u in users if u != user])
            interaction_type = np.random.choice(interaction_types, p=[0.7, 0.2, 0.1])
            timestamp = start_date + timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            interactions.append({
                'user_id': user,
                'target_user': target,
                'interaction_type': interaction_type,
                'timestamp': timestamp.isoformat()
            })
    
    # Casual users
    for user in casual_users:
        n_interactions = np.random.randint(5, 20)
        for _ in range(n_interactions):
            target = np.random.choice([u for u in users if u != user])
            interaction_type = np.random.choice(interaction_types, p=[0.8, 0.1, 0.1])
            timestamp = start_date + timedelta(
                days=np.random.randint(0, 30),
                hours=np.random.randint(0, 24),
                minutes=np.random.randint(0, 60)
            )
            interactions.append({
                'user_id': user,
                'target_user': target,
                'interaction_type': interaction_type,
                'timestamp': timestamp.isoformat()
            })
    
    return interactions

def test_script():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create test data
        interactions = create_data()
        
        # Save interaction data
        data_file = os.path.join(tmpdir, 'interactions.json')
        with open(data_file, 'w') as f:
            json.dump(interactions, f)
        
        output_file = os.path.join(tmpdir, 'results.json')
        
        # Test different argument name variations
        possible_args = [
            ['--input_data', data_file, '--output_file', output_file, '--top_n', '10'],
            ['--input', data_file, '--output', output_file, '--top_n', '10'],
            ['--data', data_file, '--output_file', output_file, '--n', '10'],
            [data_file, output_file, '10']  # positional args
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run(['python', 'generated.py'] + args, 
                                      capture_output=True, text=True, cwd=tmpdir)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        print(f"PASS: Script execution successful: {success}")
        
        if not success:
            print("FAIL: Could not execute script with any argument variation")
            return
        
        # Check if output file exists
        output_exists = os.path.exists(output_file)
        print(f"PASS: Output file created: {output_exists}")
        
        if not output_exists:
            print("FAIL: No output file generated")
            return
        
        # Load and validate results
        try:
            with open(output_file, 'r') as f:
                results = json.load(f)
            json_valid = True
        except:
            json_valid = False
        
        print(f"PASS: Valid JSON output: {json_valid}")
        
        if not json_valid:
            return
        
        # Test structure requirements
        has_top_influencers = 'top_influencers' in results
        print(f"PASS: Contains top_influencers: {has_top_influencers}")
        
        has_user_metrics = 'user_metrics' in results
        print(f"PASS: Contains user_metrics: {has_user_metrics}")
        
        has_summary_stats = 'summary_statistics' in results
        print(f"PASS: Contains summary_statistics: {has_summary_stats}")
        
        # Test top influencers structure
        if has_top_influencers:
            top_inf = results['top_influencers']
            correct_length = len(top_inf) == 10
            print(f"PASS: Top influencers list has correct length (10): {correct_length}")
            
            if len(top_inf) > 0:
                has_required_fields = all(
                    'user_id' in inf and 'combined_score' in inf 
                    for inf in top_inf
                )
                print(f"PASS: Top influencers have required fields: {has_required_fields}")
                
                # Check if sorted by combined score (descending)
                scores = [inf['combined_score'] for inf in top_inf]
                is_sorted = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
                print(f"PASS: Top influencers sorted by score: {is_sorted}")
            else:
                print("FAIL: Empty top influencers list")
                has_required_fields = False
                is_sorted = False
        
        # Test user metrics
        if has_user_metrics:
            user_metrics = results['user_metrics']
            has_influence_scores = any('influence_score' in metrics for metrics in user_metrics.values())
            print(f"PASS: User metrics contain influence scores: {has_influence_scores}")
            
            has_centrality = any('centrality' in metrics for metrics in user_metrics.values())
            print(f"PASS: User metrics contain centrality: {has_centrality}")
        
        # Test summary statistics
        if has_summary_stats:
            summary = results['summary_statistics']
            has_interaction_counts = 'total_interactions_by_type' in summary
            print(f"PASS: Summary contains interaction type counts: {has_interaction_counts}")
            
            has_avg_interactions = 'average_interactions_per_user' in summary
            print(f"PASS: Summary contains average interactions per user: {has_avg_interactions}")
        
        # Calculate accuracy scores
        df = pd.DataFrame(interactions)
        
        # Expected top users (power users should rank high)
        expected_top_users = [f"user_{i:03d}" for i in range(5)]
        
        if has_top_influencers and len(results['top_influencers']) > 0:
            actual_top_5 = [inf['user_id'] for inf in results['top_influencers'][:5]]
            top_user_accuracy = len(set(expected_top_users) & set(actual_top_5)) / 5
        else:
            top_user_accuracy = 0
        
        print(f"SCORE: Top influencer identification accuracy: {top_user_accuracy:.3f}")
        
        # Score influence calculation reasonableness
        if has_user_metrics:
            user_metrics = results['user_metrics']
            # Check if power users have higher influence scores
            power_user_scores = []
            regular_user_scores = []
            
            for user_id, metrics in user_metrics.items():
                if 'influence_score' in metrics:
                    if user_id in expected_top_users:
                        power_user_scores.append(metrics['influence_score'])
                    else:
                        regular_user_scores.append(metrics['influence_score'])
            
            if power_user_scores and regular_user_scores:
                avg_power_score = np.mean(power_user_scores)
                avg_regular_score = np.mean(regular_user_scores)
                influence_score_quality = min(1.0, max(0.0, 
                    (avg_power_score - avg_regular_score) / max(avg_power_score, 1)))
            else:
                influence_score_quality = 0
        else:
            influence_score_quality = 0
        
        print(f"SCORE: Influence score calculation quality: {influence_score_quality:.3f}")

if __name__ == "__main__":
    test_script()
