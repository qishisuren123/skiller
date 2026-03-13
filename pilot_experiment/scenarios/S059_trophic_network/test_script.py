import os
import sys
import subprocess
import tempfile
import json
import numpy as np
import pandas as pd
from scipy import sparse
import matplotlib.pyplot as plt
import networkx as nx

def create_data():
    """Generate synthetic trophic network data"""
    np.random.seed(42)
    
    # Create a realistic food web with 20 species
    species = [f"species_{i:02d}" for i in range(20)]
    
    # Define trophic groups
    producers = species[:6]  # Primary producers
    herbivores = species[6:12]  # Primary consumers
    carnivores = species[12:17]  # Secondary consumers
    top_predators = species[17:20]  # Top predators
    
    interactions = []
    
    # Herbivores eat producers
    for herb in herbivores:
        for prod in producers:
            if np.random.random() < 0.4:  # 40% chance of interaction
                strength = np.random.uniform(0.3, 0.9)
                interactions.append([herb, prod, strength])
    
    # Carnivores eat herbivores
    for carn in carnivores:
        for herb in herbivores:
            if np.random.random() < 0.3:
                strength = np.random.uniform(0.4, 0.8)
                interactions.append([carn, herb, strength])
    
    # Top predators eat carnivores and some herbivores
    for top in top_predators:
        for carn in carnivores:
            if np.random.random() < 0.25:
                strength = np.random.uniform(0.5, 0.9)
                interactions.append([top, carn, strength])
        for herb in herbivores:
            if np.random.random() < 0.15:
                strength = np.random.uniform(0.3, 0.7)
                interactions.append([top, herb, strength])
    
    # Some omnivory - carnivores eating producers
    for carn in carnivores:
        for prod in producers:
            if np.random.random() < 0.1:
                strength = np.random.uniform(0.2, 0.5)
                interactions.append([carn, prod, strength])
    
    df = pd.DataFrame(interactions, columns=['predator', 'prey', 'interaction_strength'])
    return df

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create test data
        interactions_df = create_data()
        interactions_df.to_csv('interactions.csv', index=False)
        
        # Run the generated script
        cmd = [
            sys.executable, 'generated.py',
            '--input', 'interactions.csv',
            '--output', 'results.json',
            '--plot', 'network.png'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            print("FAIL: Script timed out")
            return
        except FileNotFoundError:
            print("FAIL: generated.py not found")
            return
        
        if result.returncode != 0:
            print(f"FAIL: Script failed with return code {result.returncode}")
            print(f"STDERR: {result.stderr}")
            return
        
        # Test 1: Check if results.json exists and is valid JSON
        try:
            with open('results.json', 'r') as f:
                results = json.load(f)
            print("PASS: Results JSON file created and valid")
        except:
            print("FAIL: Results JSON file missing or invalid")
            return
        
        # Test 2: Check if network plot exists
        if os.path.exists('network.png'):
            print("PASS: Network plot file created")
        else:
            print("FAIL: Network plot file missing")
        
        # Test 3: Check if trophic levels are present
        if 'trophic_levels' in results:
            trophic_levels = results['trophic_levels']
            print("PASS: Trophic levels calculated")
        else:
            print("FAIL: Trophic levels missing from results")
            return
        
        # Test 4: Check if all species have trophic levels
        all_species = set(interactions_df['predator']).union(set(interactions_df['prey']))
        if set(trophic_levels.keys()) == all_species:
            print("PASS: All species have trophic levels")
        else:
            print("FAIL: Missing trophic levels for some species")
        
        # Test 5: Check if trophic levels are reasonable (>= 1)
        tl_values = list(trophic_levels.values())
        if all(tl >= 1.0 for tl in tl_values):
            print("PASS: All trophic levels >= 1")
        else:
            print("FAIL: Some trophic levels < 1")
        
        # Test 6: Check if primary producers have trophic level 1
        producers = []
        prey_set = set(interactions_df['prey'])
        predator_set = set(interactions_df['predator'])
        producers = prey_set - predator_set  # Species that are prey but never predators
        
        if producers and all(abs(trophic_levels[sp] - 1.0) < 0.01 for sp in producers):
            print("PASS: Primary producers have trophic level 1")
        else:
            print("FAIL: Primary producers don't have trophic level 1")
        
        # Test 7: Check network metrics presence
        required_metrics = ['connectance', 'mean_trophic_level', 'max_chain_length']
        if all(metric in results for metric in required_metrics):
            print("PASS: Required network metrics present")
        else:
            print("FAIL: Missing required network metrics")
        
        # Test 8: Check connectance value is reasonable (0-1)
        if 'connectance' in results and 0 <= results['connectance'] <= 1:
            print("PASS: Connectance value is valid")
        else:
            print("FAIL: Invalid connectance value")
        
        # Test 9: Check mean trophic level is reasonable
        if 'mean_trophic_level' in results and 1 <= results['mean_trophic_level'] <= 5:
            print("PASS: Mean trophic level is reasonable")
        else:
            print("FAIL: Mean trophic level is unreasonable")
        
        # Test 10: Check keystone species identification
        if 'keystone_species' in results and len(results['keystone_species']) >= 3:
            print("PASS: Keystone species identified")
        else:
            print("FAIL: Keystone species missing or insufficient")
        
        # Test 11: Check trophic level distribution
        if 'trophic_level_counts' in results:
            print("PASS: Trophic level distribution calculated")
        else:
            print("FAIL: Trophic level distribution missing")
        
        # Test 12: Check max chain length is reasonable
        if 'max_chain_length' in results and 1 <= results['max_chain_length'] <= 6:
            print("PASS: Maximum chain length is reasonable")
        else:
            print("FAIL: Maximum chain length is unreasonable")
        
        # Test 13: Verify trophic level consistency
        consistent = True
        for _, row in interactions_df.iterrows():
            predator_tl = trophic_levels[row['predator']]
            prey_tl = trophic_levels[row['prey']]
            if predator_tl <= prey_tl:
                consistent = False
                break
        
        if consistent:
            print("PASS: Trophic levels are consistent with predator-prey relationships")
        else:
            print("FAIL: Trophic level inconsistencies found")
        
        # Test 14: Check JSON structure completeness
        expected_keys = ['trophic_levels', 'network_metrics', 'keystone_species']
        if all(key in results for key in expected_keys):
            print("PASS: Complete JSON structure")
        else:
            print("FAIL: Incomplete JSON structure")
        
        # Test 15: Validate keystone species format
        keystone_valid = True
        if 'keystone_species' in results:
            for species_info in results['keystone_species']:
                if not isinstance(species_info, dict) or 'species' not in species_info:
                    keystone_valid = False
                    break
        else:
            keystone_valid = False
            
        if keystone_valid:
            print("PASS: Keystone species format is valid")
        else:
            print("FAIL: Invalid keystone species format")
        
        # SCORE 1: Trophic level accuracy
        # Calculate expected vs actual trophic levels for known structure
        tl_accuracy = 0.0
        if trophic_levels:
            # Check if producers are close to 1.0
            producers_score = sum(1 for sp in producers if abs(trophic_levels[sp] - 1.0) < 0.1) / max(len(producers), 1)
            
            # Check if predators have higher TL than prey
            hierarchy_score = 0
            total_interactions = 0
            for _, row in interactions_df.iterrows():
                total_interactions += 1
                if trophic_levels[row['predator']] > trophic_levels[row['prey']]:
                    hierarchy_score += 1
            
            hierarchy_score = hierarchy_score / max(total_interactions, 1)
            tl_accuracy = (producers_score + hierarchy_score) / 2
        
        print(f"SCORE: Trophic level accuracy: {tl_accuracy:.3f}")
        
        # SCORE 2: Network analysis completeness
        completeness = 0.0
        total_components = 6  # trophic_levels, connectance, mean_tl, max_chain, keystone, tl_counts
        
        if 'trophic_levels' in results and len(results['trophic_levels']) > 0:
            completeness += 1/total_components
        if 'connectance' in results and 0 <= results.get('connectance', -1) <= 1:
            completeness += 1/total_components
        if 'mean_trophic_level' in results:
            completeness += 1/total_components
        if 'max_chain_length' in results:
            completeness += 1/total_components
        if 'keystone_species' in results and len(results['keystone_species']) >= 3:
            completeness += 1/total_components
        if os.path.exists('network.png'):
            completeness += 1/total_components
            
        print(f"SCORE: Analysis completeness: {completeness:.3f}")

if __name__ == "__main__":
    run_test()
