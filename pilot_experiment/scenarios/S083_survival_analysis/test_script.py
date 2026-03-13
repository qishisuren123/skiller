import subprocess
import tempfile
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats
import sys

def create_data():
    """Generate synthetic survival data for testing"""
    np.random.seed(42)
    
    # Generate survival times from exponential distribution
    n_patients = 100
    
    # Group A (control) - shorter survival
    times_a = np.random.exponential(scale=12, size=50)  # months
    group_a = ['A'] * 50
    
    # Group B (treatment) - longer survival  
    times_b = np.random.exponential(scale=18, size=50)  # months
    group_b = ['B'] * 50
    
    times = np.concatenate([times_a, times_b])
    groups = group_a + group_b
    
    # Generate censoring (some patients lost to follow-up)
    # 30% censoring rate
    censored = np.random.binomial(1, 0.3, n_patients)
    events = 1 - censored  # 1 = event occurred, 0 = censored
    
    # For censored patients, reduce observed time
    censored_mask = censored == 1
    times[censored_mask] = times[censored_mask] * np.random.uniform(0.3, 0.8, sum(censored_mask))
    
    # Round times to 1 decimal place
    times = np.round(times, 1)
    
    return {
        'times': times.tolist(),
        'events': events.tolist(), 
        'groups': groups
    }

def run_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        
        # Create test data
        data = create_data()
        
        # Prepare arguments - try common variations
        possible_args = [
            ['--times'] + [str(t) for t in data['times']] + 
            ['--events'] + [str(e) for e in data['events']] +
            ['--groups'] + data['groups'] +
            ['--output', 'results.json', '--plot', 'survival_curve.png'],
            
            ['--survival-times'] + [str(t) for t in data['times']] + 
            ['--event-indicators'] + [str(e) for e in data['events']] +
            ['--group-labels'] + data['groups'] +
            ['--output-file', 'results.json', '--plot-file', 'survival_curve.png'],
            
            ['-t'] + [str(t) for t in data['times']] + 
            ['-e'] + [str(e) for e in data['events']] +
            ['-g'] + data['groups'] +
            ['-o', 'results.json', '-p', 'survival_curve.png']
        ]
        
        success = False
        for args in possible_args:
            try:
                result = subprocess.run([sys.executable, 'generated.py'] + args, 
                                      capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    success = True
                    break
            except:
                continue
        
        if not success:
            print("FAIL: Script execution failed with all argument variations")
            return
            
        print("PASS: Script executed successfully")
        
        # Test file outputs
        if os.path.exists('results.json'):
            print("PASS: JSON results file created")
        else:
            print("FAIL: JSON results file not created")
            return
            
        if os.path.exists('survival_curve.png'):
            print("PASS: Survival curve plot created")
        else:
            print("FAIL: Survival curve plot not created")
            
        # Load and validate results
        try:
            with open('results.json', 'r') as f:
                results = json.load(f)
            print("PASS: JSON file is valid")
        except:
            print("FAIL: JSON file is invalid or unreadable")
            return
            
        # Test required fields in results
        required_fields = ['survival_probabilities', 'median_survival', 'confidence_intervals']
        for field in required_fields:
            if field in results:
                print(f"PASS: {field} present in results")
            else:
                print(f"FAIL: {field} missing from results")
                
        # Test survival probabilities
        if 'survival_probabilities' in results:
            surv_probs = results['survival_probabilities']
            if isinstance(surv_probs, (list, dict)) and len(surv_probs) > 0:
                print("PASS: Survival probabilities computed")
                
                # Check if probabilities are in valid range
                if isinstance(surv_probs, list):
                    probs = surv_probs
                else:
                    probs = list(surv_probs.values())
                    
                valid_probs = all(0 <= p <= 1 for p in probs if isinstance(p, (int, float)))
                if valid_probs:
                    print("PASS: Survival probabilities in valid range [0,1]")
                else:
                    print("FAIL: Survival probabilities outside valid range")
            else:
                print("FAIL: Survival probabilities not properly computed")
        else:
            print("FAIL: Survival probabilities missing")
            
        # Test median survival
        if 'median_survival' in results:
            median_surv = results['median_survival']
            if isinstance(median_surv, (dict, float, int)):
                print("PASS: Median survival computed")
            else:
                print("FAIL: Median survival not properly computed")
        else:
            print("FAIL: Median survival missing")
            
        # Test confidence intervals
        if 'confidence_intervals' in results:
            ci = results['confidence_intervals']
            if isinstance(ci, (dict, list)) and len(ci) > 0:
                print("PASS: Confidence intervals computed")
            else:
                print("FAIL: Confidence intervals not properly computed")
        else:
            print("FAIL: Confidence intervals missing")
            
        # Test group analysis
        if 'groups' in results or 'group_analysis' in results:
            print("PASS: Group-wise analysis performed")
        else:
            print("FAIL: Group-wise analysis missing")
            
        # Test at-risk numbers
        if 'at_risk' in results or 'number_at_risk' in results:
            print("PASS: At-risk numbers computed")
        else:
            print("FAIL: At-risk numbers missing")
            
        # SCORE: Statistical accuracy
        # Check if survival probabilities decrease monotonically (approximately)
        score1 = 0.0
        if 'survival_probabilities' in results:
            surv_probs = results['survival_probabilities']
            if isinstance(surv_probs, dict):
                times_sorted = sorted([float(t) for t in surv_probs.keys()])
                probs_sorted = [surv_probs[str(t)] for t in times_sorted]
                
                # Check monotonic decrease (allowing small violations)
                violations = sum(1 for i in range(1, len(probs_sorted)) 
                               if probs_sorted[i] > probs_sorted[i-1] + 0.01)
                score1 = max(0, 1 - violations / len(probs_sorted))
            elif isinstance(surv_probs, list) and len(surv_probs) > 1:
                violations = sum(1 for i in range(1, len(surv_probs)) 
                               if surv_probs[i] > surv_probs[i-1] + 0.01)
                score1 = max(0, 1 - violations / len(surv_probs))
                
        print(f"SCORE: {score1:.3f} (survival curve monotonicity)")
        
        # SCORE: Completeness of analysis
        score2 = 0.0
        expected_components = [
            'survival_probabilities', 'median_survival', 'confidence_intervals',
            ('groups', 'group_analysis'), ('at_risk', 'number_at_risk')
        ]
        
        components_found = 0
        for component in expected_components:
            if isinstance(component, tuple):
                if any(c in results for c in component):
                    components_found += 1
            else:
                if component in results:
                    components_found += 1
                    
        score2 = components_found / len(expected_components)
        print(f"SCORE: {score2:.3f} (analysis completeness)")

if __name__ == "__main__":
    run_test()
